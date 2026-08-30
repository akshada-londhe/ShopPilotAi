import logging
import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from app.chains.matcher import MatchedProduct
from app.llm_factory import build_llm
from app.models.query import NormalizedQuery
from app.observability.langfuse_setup import get_langfuse_handler

logger = logging.getLogger(__name__)


SYNTHESIZER_PROMPT = ChatPromptTemplate.from_template(
    """Write a concise, helpful verdict explaining why the TOP PICK is the best
choice for the buyer, and briefly how it compares to the other options.

Buyer wanted: {category} under {budget_max} {currency}, constraints: {constraints}, use case: {use_case}

TOP PICK:
{top_pick}

OTHER OPTIONS considered:
{alternatives}

Rules:
1. Write 3-4 clear, conversational sentences.
2. First say why the TOP PICK fits the buyer (price, constraints met, use case).
3. Then explicitly COMPARE it to at least one other option by name, using only
   the facts given, e.g. "chosen over the boAt Rockerz (₹2,199) because it adds
   noise cancellation within budget". If no other options are listed, skip the
   comparison instead of inventing one.
4. Every product claim MUST cite its source URL in parentheses right after the
   product, e.g. "the Logitech G102 (https://...)".
5. Only use the source URLs provided above. Never invent a URL, a price, a spec,
   or a competing product that is not listed above. State only what is given.
"""
)


def build_synthesizer_chain() -> Runnable:
    """Primary synthesis chain using the configured provider."""
    llm = build_llm("synthesizer", temperature=0.4)

    return SYNTHESIZER_PROMPT | llm | StrOutputParser()


def build_fallback_synthesizer_chain() -> Runnable:
    """Fallback synthesis chain using the independent fallback provider."""
    llm = build_llm("synthesizer_fallback", temperature=0.4)

    return SYNTHESIZER_PROMPT | llm | StrOutputParser()


def _evidence_line(m: MatchedProduct) -> str:
    """One evidence line: name, real price (or 'unlisted'), specs, constraints, url."""
    name = m.product.get_name()
    price = m.product.get_price()
    specs = [
        str(f.value)
        for k, f in m.product.fields.items()
        if k.startswith("spec_")
    ]
    spec_summary = ", ".join(specs[:3]) if specs else "standard specifications"

    name_field = m.product.fields.get("name")
    source_url = name_field.source_url if name_field else ""
    if not source_url:
        for f in m.product.fields.values():
            if f.source_url:
                source_url = f.source_url
                break

    constraints = ", ".join(m.matched_constraints) if m.matched_constraints else "none listed"
    price_text = f"₹{price}" if price is not None else "unlisted"
    return (
        f"- {name} (Price: {price_text}, Specs: {spec_summary}, "
        f"meets: {constraints}) source: {source_url}"
    )


def _format_top_pick(matched: list[MatchedProduct]) -> str:
    if not matched:
        return "No products found."
    return _evidence_line(matched[0])


def _format_alternatives(matched: list[MatchedProduct]) -> str:
    """Runner-up options (2nd and 3rd) for the comparative explanation."""
    others = matched[1:3]
    if not others:
        return "None — only one candidate was verified."
    return "\n".join(_evidence_line(m) for m in others)


def _clean_verdict(text: str) -> str:
    """Tidy whitespace while preserving source-URL citations (spec FR11)."""
    # Convert any markdown links [text](url) into "text (url)" so the citation
    # survives as a plain URL rather than being hidden behind link syntax.
    cleaned = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'\1 (\2)', text)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()
    return cleaned


def synthesize_answer(matched: list[MatchedProduct], query: NormalizedQuery) -> str:
    """Synthesize a clean buyer-facing verdict paragraph without URLs."""
    payload = {
        "category": query.category,
        "budget_max": query.budget.max,
        "currency": query.budget.currency,
        "constraints": ", ".join(query.constraints) or "none",
        "use_case": query.use_case,
        "top_pick": _format_top_pick(matched),
        "alternatives": _format_alternatives(matched),
    }

    # Primary: Groq
    try:
        chain = build_synthesizer_chain()
        raw = chain.invoke(
            payload,
            config={"callbacks": [get_langfuse_handler()]},
        )
        return _clean_verdict(raw)

    except Exception:
        logger.warning(
            "Primary Groq synthesis failed, falling back to a second Groq model",
            exc_info=True,
        )

    # Fallback: second Groq model
    try:
        fallback_chain = build_fallback_synthesizer_chain()
        raw = fallback_chain.invoke(
            payload,
            config={"callbacks": [get_langfuse_handler()]},
        )
        return _clean_verdict(raw)

    except Exception:
        logger.exception("Groq fallback synthesis failed")
        if matched:
            top = matched[0].product.get_name()
            return f"Based on your requirements, the {top} is our top verified recommendation within your specified budget."
        return "No matching products could be verified against all constraints."
