from dataclasses import dataclass, field
import re

from app.observability.langfuse_setup import get_langfuse_handler
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from pydantic import BaseModel
from app.retry_utils import with_provider_retry
from app.llm_factory import build_llm
from app.models.product import ProductEntity
from app.models.query import NormalizedQuery

SOFT_MATCH_PROMPT = ChatPromptTemplate.from_template(
    """Rate how well this product matches the buyer's soft preferences, on a 0-10 scale.

Product: {product_name}
Product specs: {product_specs}

Buyer's preferences (subjective qualities, not hard requirements): {preferences}

Return a single integer score 0-10. 10 means the product strongly matches the
preferences based on its specs. 0 means no evidence of matching. Do not invent
specs that are not listed above.

Return only valid JSON with a numeric score field.
"""
)


class _SoftScore(BaseModel):
    score: int


def build_matcher_chain(provider_override: str | None = None) -> Runnable:
    llm = build_llm("matcher", provider_override=provider_override)
    structured_llm = llm.with_structured_output(_SoftScore, method="json_mode")
    return SOFT_MATCH_PROMPT | structured_llm


@dataclass
class MatchedProduct:
    product: ProductEntity
    soft_score: float = 0.0
    matched_constraints: list[str] = field(default_factory=list)


def _product_source(product: ProductEntity) -> str:
    name_field = product.fields.get("name")
    if name_field and name_field.source_url:
        return name_field.source_url
    for f in product.fields.values():
        if f.source_url:
            return f.source_url
    return ""


def _entity_richness(product: ProductEntity) -> tuple[bool, int]:
    """How usable an entity is: has a price, and how many spec fields.
    Used to keep the best entity when several share one source page."""
    has_price = product.get_price() is not None
    spec_count = sum(1 for k in product.fields if k.startswith("spec_"))
    return (has_price, spec_count)


def _dedupe_by_source(products: list[ProductEntity]) -> list[ProductEntity]:
    """Collapse entities that came from the same source URL, keeping the
    richest one. The extractor can emit several loosely-named 'products' from a
    single page; only the best-populated one should survive."""
    best: dict[str, ProductEntity] = {}
    order: list[str] = []
    for p in products:
        src = _product_source(p)
        key = src or f"__nourl__{p.entity_id}"
        if key not in best:
            best[key] = p
            order.append(key)
        elif _entity_richness(p) > _entity_richness(best[key]):
            best[key] = p
    return [best[k] for k in order]


# Strong accessory markers: when any of these appears in a device listing's
# TITLE, the listing is an accessory (a case/cover/cable), not the device.
# These are unambiguous — a phone's own title never contains "back cover".
# Matched as whole words/phrases (word boundaries) to avoid substring traps.
_ACCESSORY_MARKERS = (
    "case",
    "cover",
    "pouch",
    "protector",
    "skin",
    "sleeve",
    "compatible with",
    "ear pads",
    "ear cushion",
    "ear tips",
    "cable",
    "charger",
    "screen guard",
    "screen protector",
    "tempered glass",
    "keyboard skin",
    "palm rest",
    "sticker",
    "decal",
)

# Spare-part words that also occur legitimately in a real device's title
# (a phone lists its "RAM", a laptop its "battery"). These count as accessory
# signals ONLY when the listing is clearly a part sold FOR a device — i.e. it
# pairs with "replacement" or the "for <brand>" pattern. Never on their own.
_SPARE_PART_WORDS = (
    "battery",
    "ram",
    "ssd",
    "hard drive",
    "hard disk",
    "sodimm",
    "hinge",
    "lcd screen",
    "display panel",
    "motherboard",
    "fan assembly",
    "power supply",
)

# "for <brand/model>" phrasing is a strong accessory signal
# (e.g. "Battery for Dell XPS 15", "Case for Sony WH-1000XM4").
_ACCESSORY_FOR_PATTERN = re.compile(
    r"\bfor\s+(dell|hp|lenovo|asus|acer|msi|sony|apple|samsung|logitech|"
    r"razer|bose|jbl|boat|xps|alienware|precision|thinkpad|macbook|inspiron|"
    r"vivobook|ideapad|nitro|victus|rog|legion)\b",
    re.IGNORECASE,
)

# Categories that name an actual device (so accessory-filtering applies).
_DEVICE_CATEGORY_HINTS = (
    "headphone",
    "earbud",
    "earphone",
    "laptop",
    "phone",
    "mouse",
    "keyboard",
    "watch",
    "speaker",
    "monitor",
    "tablet",
    "tv",
    "camera",
    "console",
)


def _accessory_scan_text(product: ProductEntity) -> str:
    """Text used to decide if a listing is an accessory.

    Prefer the UNTOUCHED scraped title (raw_title): name-cleaning strips the
    very words ("Back Cover", "Case", "Cover") that mark an accessory, so the
    cleaned name alone is blind to them. Fall back to the cleaned name for
    older entities that predate raw_title.

    We deliberately scan only TITLE text, never the free-text snippet: markers
    like "battery" or "charging" legitimately appear in a real device's
    description and would cause false accessory matches. Titles are precise.
    """
    parts: list[str] = []
    raw_title_field = product.fields.get("raw_title")
    if raw_title_field:
        parts.append(str(raw_title_field.value))
    parts.append(product.get_name())
    return " ".join(parts).lower()


def _is_accessory_for_device(product: ProductEntity, query: NormalizedQuery) -> bool:
    """True if this listing is an accessory while the buyer asked for a device."""
    category = (query.category or "").lower()
    if not any(hint in category for hint in _DEVICE_CATEGORY_HINTS):
        return False  # buyer may actually want an accessory; don't filter
    # If the category word itself is the accessory (e.g. category "phone case"),
    # don't filter.
    if any(marker in category for marker in _ACCESSORY_MARKERS):
        return False
    text = _accessory_scan_text(product)

    # Strong markers: whole-word match so "ramble" never matches "ram" and
    # "case" only matches the word, not a substring.
    for marker in _ACCESSORY_MARKERS:
        if re.search(rf"\b{re.escape(marker)}\b", text):
            return True

    # "<something> for Dell XPS 15" style listings are accessories/spares.
    if _ACCESSORY_FOR_PATTERN.search(text):
        return True

    # Spare-part words are accessory signals only when the listing is clearly a
    # part sold for a device: it says "replacement", or "<part> for <brand>".
    has_spare_word = any(
        re.search(rf"\b{re.escape(w)}\b", text) for w in _SPARE_PART_WORDS
    )
    if has_spare_word and ("replacement" in text or _ACCESSORY_FOR_PATTERN.search(text)):
        return True

    return False


def _passes_hard_constraints(product: ProductEntity, query: NormalizedQuery) -> bool:
    """Phase 1: programmatic checks. No LLM call. Spec FR8."""
    if _is_accessory_for_device(product, query):
        return False
    price = product.get_price()
    if price is not None:
        if price <= 0:
            return False
        if price > query.budget.max:
            return False
        if price < query.budget.min:
            return False
    return True


_STOPWORDS = {"with", "and", "for", "the", "a", "an", "of", "in", "to", "good"}


def _constraint_tokens(constraint: str) -> list[str]:
    """Significant lowercase tokens of a constraint (drop stopwords/short bits)."""
    return [
        t
        for t in re.findall(r"[a-z0-9]+", constraint.lower())
        if t not in _STOPWORDS and len(t) > 1
    ]


def _matched_constraint_names(
    product: ProductEntity, query: NormalizedQuery
) -> list[str]:
    """Which explicit hard constraints does this product mention?

    Token-based: a constraint counts as matched when every significant token in
    it appears somewhere in the product's name or spec text. This lets
    "white color" or "bluetooth 4" match even when phrased differently, where a
    raw substring check would miss them.
    """
    spec_text = " ".join(
        str(f.value).lower()
        for name, f in product.fields.items()
        if name.startswith("spec_")
    )
    full_text = f"{product.get_name().lower()} {spec_text}"
    matched = []
    for c in query.constraints:
        tokens = _constraint_tokens(c)
        if tokens and all(tok in full_text for tok in tokens):
            matched.append(c)
    return matched


def _calculate_baseline_score(product: ProductEntity, query: NormalizedQuery, matched_constraints: list[str]) -> float:
    """Calculate an intelligent heuristic baseline score (7.0 - 9.5)."""
    score = 7.0
    name = product.get_name().lower()
    
    # Category / use-case relevance
    if query.category and query.category.lower() in name:
        score += 0.8
    if query.use_case and query.use_case.lower() in name:
        score += 0.6
        
    # Hard constraint matches
    score += len(matched_constraints) * 0.5

    # Specs completeness
    spec_count = sum(1 for k in product.fields if k.startswith("spec_"))
    if spec_count >= 3:
        score += 0.4

    # Valid verified price
    price = product.get_price()
    if price and price > 0 and price <= query.budget.max:
        score += 0.5

    return min(9.5, max(6.0, round(score, 1)))


@with_provider_retry
def match_products(
    products: list[ProductEntity], query: NormalizedQuery
) -> list[MatchedProduct]:
    # Phase 1: programmatic hard-constraint filtering
    survivors = [p for p in products if _passes_hard_constraints(p, query)]
    survivors = _dedupe_by_source(survivors)

    # Prefer products that actually have a real, scraped price so the buyer
    # always sees a price with the recommendation. When ANY priced candidate
    # survives, keep only priced ones (the best match is then guaranteed to
    # carry a real price). Prices are never fabricated. Only if NOTHING is
    # priced do we fall back to price-less matches rather than return empty
    # (graceful degradation, since Tavily often can't scrape prices).
    priced = [p for p in survivors if p.get_price() is not None]
    if priced:
        survivors = priced

    matched: list[MatchedProduct] = []
    for p in survivors:
        c_names = _matched_constraint_names(p, query)
        base_score = _calculate_baseline_score(p, query, c_names)
        matched.append(MatchedProduct(product=p, soft_score=base_score, matched_constraints=c_names))

    # Phase 2: LLM scoring if specific soft preferences were provided
    if query.preferences and matched:
        from concurrent.futures import ThreadPoolExecutor

        def _score_single_product(m: MatchedProduct, chain: Runnable):
            spec_text = ", ".join(
                str(f.value)
                for name, f in m.product.fields.items()
                if name.startswith("spec_")
            )
            try:
                result = chain.invoke(
                    {
                        "product_name": m.product.get_name(),
                        "product_specs": spec_text or "no specs available",
                        "preferences": ", ".join(query.preferences),
                    },
                    config={"callbacks": [get_langfuse_handler()]},
                )
                if hasattr(result, "score") and result.score > 0:
                    m.soft_score = round((m.soft_score + float(result.score)) / 2, 1)
            except Exception:
                pass

        try:
            chain = build_matcher_chain()
            with ThreadPoolExecutor(max_workers=min(4, len(matched))) as executor:
                list(executor.map(lambda m: _score_single_product(m, chain), matched))
        except Exception:
            pass  # Retain baseline score if provider fails

    # Rank by how well it matches the request: number of hard constraints met,
    # then soft score. Price PRESENCE is deliberately NOT a ranking signal:
    # Tavily rarely exposes prices, so a priced accessory must never outrank a
    # price-less real match. Relevance wins, not whether a price happened to
    # be scrapable.
    matched.sort(
        key=lambda m: (len(m.matched_constraints), m.soft_score),
        reverse=True,
    )
    return matched
