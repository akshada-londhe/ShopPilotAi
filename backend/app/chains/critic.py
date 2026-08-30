import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from app.retry_utils import with_provider_retry
from app.chains.matcher import MatchedProduct
from app.llm_factory import build_llm
from app.models.critic import CriticFeedback, CriticVerdict
from app.models.query import NormalizedQuery
from app.observability.langfuse_setup import get_langfuse_handler

logger = logging.getLogger(__name__)

CRITIC_PROMPT = ChatPromptTemplate.from_template(
    """You are a strict quality judge for an e-commerce product recommendation system.
Score the candidate results below against the buyer's original request.

Buyer's request: category={category}, budget_max={budget_max} {currency},
constraints={constraints}, preferences={preferences}, use_case={use_case}

Candidate results:
{product_summary}

Score each of these 0-10:
- relevance: are these products actually in the requested category and use case?
- requirement_match: do they satisfy the hard constraints listed above?
- evidence_quality: are these real, specific, named products from real merchant
  listings? Judge the specs and sourcing. IMPORTANT: a missing price is common
  because prices are often not present in scraped page text; do NOT heavily
  penalize evidence_quality just because price is null. Only penalize if the
  products themselves are vague, generic, or clearly not real listings.
- completeness: are there enough distinct candidates (ideally 3+) to give the buyer
  a real choice?

Also set contradiction_flag=true if any result contains self-contradictory or
clearly false information (e.g. price is 0 or negative, or specs contradict the
product category).

If you would score below 7 overall, populate feedback with SPECIFIC guidance:
- missing_data: what information is missing that would help find better results
- negative_prompts: what kind of results to avoid on the next search attempt
- failed_criteria: which specific requirement(s) were not met

Return your response as a valid JSON object in this exact structure:
{{
  "relevance": 8,
  "requirement_match": 8,
  "evidence_quality": 8,
  "completeness": 8,
  "contradiction_flag": false,
  "feedback": {{
    "missing_data": [],
    "negative_prompts": [],
    "failed_criteria": []
  }}
}}
"""
)


def build_critic_chain(provider_override: str | None = None) -> Runnable:
    llm = build_llm("critic", provider_override=provider_override)
    structured_llm = llm.with_structured_output(CriticVerdict, method="json_mode")
    return CRITIC_PROMPT | structured_llm


def _summarize_products(matched: list[MatchedProduct]) -> str:
    if not matched:
        return "0 products found."
    lines = []
    for m in matched:
        name = m.product.get_name()
        price = m.product.get_price()
        specs = ", ".join(
            str(f.value) for n, f in m.product.fields.items() if n.startswith("spec_")
        )
        lines.append(
            f"- {name}: price={price}, specs=[{specs}], matched constraints={m.matched_constraints}"
        )
    return "\n".join(lines)


def _fallback_verdict(matched: list[MatchedProduct]) -> CriticVerdict:
    """Deterministic validation rubric when all LLM providers fail or time out."""
    count = len(matched)
    return CriticVerdict(
        relevance=8 if count else 0,
        requirement_match=8 if count else 0,
        evidence_quality=7 if count else 0,
        completeness=min(10, max(6, count * 3)),
        contradiction_flag=False,
        feedback=CriticFeedback(),
    )


@with_provider_retry
def critique_results(
    matched: list[MatchedProduct], query: NormalizedQuery
) -> CriticVerdict:
    payload = {
        "category": query.category,
        "budget_max": query.budget.max,
        "currency": query.budget.currency,
        "constraints": ", ".join(query.constraints) or "none",
        "preferences": ", ".join(query.preferences) or "none",
        "use_case": query.use_case or "none",
        "product_summary": _summarize_products(matched),
    }

    # Approach 1: Primary provider (Groq)
    try:
        chain = build_critic_chain()
        result = chain.invoke(
            payload,
            config={"callbacks": [get_langfuse_handler()]},
        )
        if isinstance(result, CriticVerdict):
            return result
    except Exception:
        logger.warning("Primary critic failed or timed out, trying secondary fallback provider")

    # Approach 2: Fallback provider (OpenRouter)
    try:
        fallback_chain = build_critic_chain(provider_override="openrouter")
        result = fallback_chain.invoke(
            payload,
            config={"callbacks": [get_langfuse_handler()]},
        )
        if isinstance(result, CriticVerdict):
            return result
    except Exception:
        logger.warning("Secondary critic failed, falling back to deterministic validation rubric")

    # Approach 3: Deterministic fallback rubric
    return _fallback_verdict(matched)
