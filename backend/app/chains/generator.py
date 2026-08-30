import logging
from typing import Any

from app.retry_utils import with_provider_retry
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field, field_validator
from app.observability.langfuse_setup import get_langfuse_handler
from app.llm_factory import build_llm
from app.models.critic import CriticFeedback
from app.models.query import NormalizedQuery

logger = logging.getLogger(__name__)


GENERATOR_PROMPT = ChatPromptTemplate.from_template(
    """You are a search-query generation system for an e-commerce product search engine.

Generate focused web-search queries based on the normalized buyer request.

Buyer requirements:
- Category: {category}
- Maximum budget: {budget_max} {currency}
- Hard constraints: {constraints}
- Preferences: {preferences}
- Use case: {use_case}

Previous critic feedback:
- Missing data: {missing_data}
- Negative prompts: {negative_prompts}
- Failed criteria: {failed_criteria}

Rules:
1. Generate concise, realistic search queries targeting specific product models on Amazon.in and Flipkart.com.
2. Formulate queries to find direct product detail pages (e.g. "<brand> <model> price amazon.in dp", "<brand> <model> flipkart.com/p/").
3. Include specific popular brand models within the category that match the budget and constraints.
4. Preserve the buyer's hard constraints and budget limit.
5. Use different brand and feature query formulations to maximize coverage of real, individual products.
6. Do not invent product specifications.
7. Avoid results matching the negative prompts.
8. Generate between 2 and 5 useful queries specifically for Amazon and Flipkart product pages.

Return your answer as valid JSON in this exact format:
{{"queries": ["Logitech G102 gaming mouse amazon.in dp", "Razer DeathAdder Essential flipkart p"]}}
"""
)


class _QueryList(BaseModel):
    """Structured output returned by the search-query generator."""

    queries: list[Any] = Field(default_factory=list)

    @field_validator("queries", mode="before")
    @classmethod
    def clean_queries(cls, val: Any) -> list[str]:
        if not isinstance(val, list):
            return [str(val)]
        cleaned = []
        for item in val:
            if isinstance(item, str):
                cleaned.append(item)
            elif isinstance(item, dict):
                cleaned.append(item.get("query") or item.get("text") or str(item))
            else:
                cleaned.append(str(item))
        return cleaned


def build_generator_chain(provider_override: str | None = None) -> Runnable:
    """Build the LLM chain responsible for generating search queries."""
    llm = build_llm("generator", provider_override=provider_override)
    structured_llm = llm.with_structured_output(_QueryList, method="json_mode")
    return GENERATOR_PROMPT | structured_llm


def _deterministic_fallback_queries(normalized: NormalizedQuery) -> list[str]:
    """Deterministic multi-variant queries if all LLMs fail or time out."""
    cat = normalized.category or "product"
    budget = f"under {int(normalized.budget.max)} {normalized.budget.currency}" if normalized.budget.max < 10000000 else ""
    constraints_str = " ".join(normalized.constraints[:2]) if normalized.constraints else ""
    use_case_str = normalized.use_case if normalized.use_case and normalized.use_case != "general" else ""

    queries = [
        f"{cat} {constraints_str} {budget} amazon.in dp".strip(),
        f"{cat} {use_case_str} {budget} flipkart.com/p/".strip(),
        f"best {cat} {constraints_str} {budget} buy online india".strip(),
    ]
    return [q for q in queries if len(q) > 3]


@with_provider_retry
def generate_search_queries(
    normalized: NormalizedQuery, feedback: CriticFeedback | None = None
) -> list[str]:
    feedback = feedback or CriticFeedback()
    result = None

    payload = {
        "category": normalized.category,
        "budget_max": normalized.budget.max,
        "currency": normalized.budget.currency,
        "constraints": ", ".join(normalized.constraints) or "none",
        "preferences": ", ".join(normalized.preferences) or "none",
        "use_case": normalized.use_case or "none",
        "missing_data": ", ".join(feedback.missing_data) or "none",
        "negative_prompts": ", ".join(feedback.negative_prompts) or "none",
        "failed_criteria": ", ".join(feedback.failed_criteria) or "none",
    }

    # Approach 1: Primary provider (Groq)
    try:
        chain = build_generator_chain()
        result = chain.invoke(
            payload,
            config={"callbacks": [get_langfuse_handler()]},
        )
    except Exception:
        logger.warning("Primary query generator failed or timed out, trying secondary fallback provider")

    # Approach 2: Fallback provider (OpenRouter)
    if result is None:
        try:
            fallback_chain = build_generator_chain(provider_override="openrouter")
            result = fallback_chain.invoke(
                payload,
                config={"callbacks": [get_langfuse_handler()]},
            )
        except Exception:
            logger.warning("Secondary query generator failed, using deterministic query generation")

    if isinstance(result, _QueryList):
        queries = result.queries
    elif isinstance(result, dict):
        queries = result.get("queries", [])
    elif result is not None:
        queries = getattr(result, "queries", [])
    else:
        queries = []

    cleaned_queries: list[str] = []
    seen: set[str] = set()

    for item in queries:
        if not isinstance(item, str):
            continue

        cleaned = item.strip()
        if not cleaned:
            continue

        norm_key = cleaned.lower()
        if norm_key in seen:
            continue

        seen.add(norm_key)
        cleaned_queries.append(cleaned)

    # Approach 3: If no valid queries produced, use deterministic fallback
    if not cleaned_queries:
        cleaned_queries = _deterministic_fallback_queries(normalized)

    logger.info("Generated %d search queries", len(cleaned_queries))
    return cleaned_queries
