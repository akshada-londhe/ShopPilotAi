import logging
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from app.observability.langfuse_setup import get_langfuse_handler

from app.llm_factory import build_llm
from app.models.query import Budget, NormalizedQuery
from app.retry_utils import with_provider_retry

logger = logging.getLogger(__name__)


NORMALIZER_PROMPT = ChatPromptTemplate.from_template(
    """You are a query normalization system for an e-commerce product search engine.

Extract structured information from the user's query below.

Follow these rules:

- intent: what the user wants to do (usually "purchase" or "compare")
- category: the product category (e.g. "laptop", "earbuds", "gaming mouse")
- budget: min and max in the currency mentioned, default currency INR if unspecified.
  If no budget is mentioned, set max to a very high number like 10000000 and min to 0.
- constraints: hard requirements the user explicitly stated
  (e.g. "must have noise cancellation")
- preferences: soft, nice-to-have qualities
  (e.g. "prefers lightweight design")
- use_case: what the product will be used for
  (e.g. "commute", "gaming", "video editing")
- confidence_score: your confidence (0.0 to 1.0) that you extracted the user's intent correctly.

Use LOW confidence (below 0.6) when:
- the query is vague
- category is missing
- budget is missing and category is missing
- the query contains a single ambiguous word

Use HIGH confidence when:
- category + budget are clear
- category + explicit constraints are clear

Return only valid JSON matching the requested schema.

User query: {query}

Previous clarification context (if any):
{clarification_context}
"""
)


def build_normalizer_chain(provider_override: str | None = None) -> Runnable:
    llm = build_llm("normalizer", provider_override=provider_override)
    structured_llm = llm.with_structured_output(NormalizedQuery, method="json_mode")
    return NORMALIZER_PROMPT | structured_llm


def _heuristic_fallback_normalize(query: str) -> NormalizedQuery:
    """Deterministic rule-based normalizer if all LLM calls fail or time out."""
    lower = query.lower()
    
    # 1. Budget extraction
    max_budget = 10000000.0
    price_match = re.search(r"(?:under|below|less than|<|within|budget of)\s*(?:₹|rs\.?|inr)?\s*([0-9,]+|\d+k|\d+lakh|\d+l)", lower)
    if not price_match:
        price_match = re.search(r"(?:₹|rs\.?|inr)\s*([0-9,]+|\d+k|\d+lakh|\d+l)", lower)
    if not price_match:
        price_match = re.search(r"\b([0-9]{3,7})\b", lower)

    if price_match:
        raw_val = price_match.group(1).replace(",", "").strip()
        if "k" in raw_val:
            try:
                max_budget = float(raw_val.replace("k", "")) * 1000
            except ValueError:
                pass
        elif "lakh" in raw_val or "l" in raw_val:
            try:
                max_budget = float(re.sub(r"[a-z]", "", raw_val)) * 100000
            except ValueError:
                pass
        else:
            try:
                max_budget = float(raw_val)
            except ValueError:
                pass

    # 2. Category extraction
    known_categories = [
        "gaming mouse", "wireless mouse", "mouse",
        "wireless earbuds", "earbuds", "earphones", "headphones",
        "gaming laptop", "laptop", "macbook",
        "mechanical keyboard", "keyboard",
        "smartphone", "mobile phone", "phone",
        "smartwatch", "watch",
        "monitor", "tv", "speaker", "tablet", "ipad"
    ]
    category = "products"
    for cat in known_categories:
        if cat in lower:
            category = cat
            break

    # 3. Use-case extraction
    use_case = "general"
    for uc in ["gaming", "coding", "editing", "commute", "office", "travel", "sports", "fitness"]:
        if uc in lower:
            use_case = uc
            break

    # 4. Constraints extraction
    constraints = []
    for c in ["anc", "noise cancellation", "wireless", "rgb", "bluetooth", "lightweight", "oled", "144hz", "16gb", "type c"]:
        if c in lower:
            constraints.append(c)

    # High confidence if category is recognized or non-empty query provided
    confidence = 0.85 if (category != "products" or len(query.strip()) > 3) else 0.3

    return NormalizedQuery(
        intent="purchase",
        category=category if category != "products" else (query.strip() or "products"),
        budget=Budget(min=0, max=int(max_budget), currency="INR"),
        constraints=constraints,
        preferences=[],
        use_case=use_case,
        confidence_score=confidence,
    )


@with_provider_retry
def normalize_query(query: str, clarification_context: str = "none") -> NormalizedQuery:
    # Approach 1: Primary provider (Groq)
    try:
        chain = build_normalizer_chain()
        result = chain.invoke(
            {"query": query, "clarification_context": clarification_context},
            config={"callbacks": [get_langfuse_handler()]},
        )
        if isinstance(result, NormalizedQuery):
            return result
    except Exception:
        logger.warning("Primary normalizer failed or timed out, trying secondary fallback provider")

    # Approach 2: Fallback provider (OpenRouter)
    try:
        fallback_chain = build_normalizer_chain(provider_override="openrouter")
        result = fallback_chain.invoke(
            {"query": query, "clarification_context": clarification_context},
            config={"callbacks": [get_langfuse_handler()]},
        )
        if isinstance(result, NormalizedQuery):
            return result
    except Exception:
        logger.warning("Secondary normalizer failed, falling back to deterministic heuristic normalization")

    # Approach 3: Deterministic heuristic normalization
    return _heuristic_fallback_normalize(query)
