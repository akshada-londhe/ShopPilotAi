import logging
import uuid
from datetime import datetime, timedelta, timezone

from app.retry_utils import with_provider_retry
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from pydantic import AliasChoices, BaseModel, Field

from app.observability.langfuse_setup import get_langfuse_handler
from app.llm_factory import build_llm
from app.models.product import ExtractedField, ProductEntity
from app.retrieval.sanitizer import sanitize_content
from app.retrieval.tavily_client import TavilySearchResult


logger = logging.getLogger(__name__)


EXTRACTOR_PROMPT = ChatPromptTemplate.from_template(
    """Extract structured product information from this e-commerce web page.
A product detail page is about ONE main product. Extract that single primary
product, the item the page is selling, not related/recommended/"customers also
bought" items.

Extract ONLY what is literally stated in the text. Do NOT infer or guess values.
If the price is not clearly stated, set price to null. Never return 0 for price.

Content:
{content}

Rules:
1. Return exactly ONE product: the main item on this page. Do not list
   accessories, suggested items, or comparison products.
2. Product name: a clean brand + model name, 3 to 7 words
   (e.g. "Sony WH-1000XM4 Wireless Headphones"). Do NOT dump bullet points or
   full spec lists into the name.
3. Price: the actual current selling price as a number, or null if not stated.
   Look for the main buy-box / current price, ignore EMI and crossed-out MRP.
4. Specs: 3 to 6 concise individual specifications/features (color, connectivity,
   battery, etc.), each a short phrase. Ignore navigation, shipping, and date text.

Return only valid JSON in this exact shape:
{{"products": [{{"name": "...", "price": null, "specs": ["spec1", "spec2"]}}]}}
The products array must contain exactly one product.
"""
)


class _RawExtraction(BaseModel):
    name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("name", "product_name"),
    )
    price: float | None = None
    specs: list[str] = Field(default_factory=list)


class _RawExtractionBatch(BaseModel):
    products: list[_RawExtraction] = Field(default_factory=list)


def build_extractor_chain(provider_override: str | None = None) -> Runnable:
    llm = build_llm("extractor", provider_override=provider_override)
    structured_llm = llm.with_structured_output(_RawExtractionBatch, method="json_mode")
    return EXTRACTOR_PROMPT | structured_llm


def _clean_extracted_name(name: str) -> str:
    """Normalize extracted name to a clean brand and model string."""
    import re
    if not name:
        return ""
    # Strip prefixes like "Title: ", "Amazon.in : ", "Buy "
    cleaned = re.sub(r"^(?:Title\s*:|Amazon(?:\.in)?\s*:|Buy)\s*", "", name, flags=re.IGNORECASE).strip()
    # Strip brackets, parentheses, price mentions
    cleaned = re.sub(r"\(.*?\)", "", cleaned)
    cleaned = re.sub(r"\[.*?\]", "", cleaned)
    cleaned = re.sub(r"(?:₹|Rs\.?|INR)\s*[\d,]+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[,|]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Split on long feature delimiters
    keywords = [" with ", " featuring ", " dual ", " triple-mode", " adjustable ", " hot-swappable", " pixart", " 12000 dpi", " lightweight", " 80hrs"]
    lower = cleaned.lower()
    cutoff = len(cleaned)
    for kw in keywords:
        idx = lower.find(kw)
        if idx != -1 and 5 < idx < cutoff:
            cutoff = idx
    cleaned = cleaned[:cutoff].strip()

    words = cleaned.split()
    if len(words) > 7:
        cleaned = " ".join(words[:7])
    return cleaned or name


def _build_product_entity(
    raw: _RawExtraction,
    source_url: str,
    snippet: str,
    raw_title: str = "",
) -> ProductEntity:
    from app.retrieval.tavily_client import clean_canonical_url
    canonical_source_url = clean_canonical_url(source_url)
    now = datetime.now(timezone.utc)

    # Spec FR4 TTL policy: price/stock/availability -> 6 hours,
    # specs/static description -> 30 days.
    price_ttl = (now + timedelta(hours=6)).isoformat()
    static_ttl = (now + timedelta(days=30)).isoformat()

    fields: dict[str, ExtractedField] = {}

    name = _clean_extracted_name(raw.name) if raw.name else None
    if not name or name.strip().lower() == "unknown product":
        # Fallback name from snippet or URL
        first_line = snippet.split("\n")[0].strip()
        if len(first_line) > 5 and not first_line.startswith("http"):
            name = _clean_extracted_name(first_line[:80])
        else:
            import urllib.parse
            path = urllib.parse.urlparse(canonical_source_url).path.strip("/").split("/")[-1]
            name = path.replace("-", " ").replace("_", " ").title()[:80] or "Product"

    # Name is static product metadata -> 30 day TTL.
    fields["name"] = ExtractedField(
        value=name,
        source_url=canonical_source_url,
        snippet=snippet,
        ttl_expires_at=static_ttl,
    )

    # Preserve the UNTOUCHED scraped title. Name-cleaning strips words like
    # "Back Cover"/"Case" that mark a listing as an accessory; downstream
    # accessory detection needs the raw signal, so keep it verbatim here.
    raw_title_text = (raw_title or "").strip() or (raw.name or "").strip()
    if raw_title_text:
        fields["raw_title"] = ExtractedField(
            value=raw_title_text,
            source_url=canonical_source_url,
            snippet=snippet,
            ttl_expires_at=static_ttl,
        )

    if raw.price is not None and float(raw.price) > 0:
        # Price/stock TTL: 6 hours (spec FR4)
        fields["price"] = ExtractedField(
            value=float(raw.price),
            source_url=source_url,
            snippet=snippet,
            ttl_expires_at=price_ttl,
        )

    for i, spec in enumerate(raw.specs):
        # Specs are static description -> 30 day TTL.
        fields[f"spec_{i}"] = ExtractedField(
            value=spec,
            source_url=source_url,
            snippet=snippet,
            ttl_expires_at=static_ttl,
        )

    # Entity-level TTL reflects the most volatile field so cache freshness
    # is gated by the shortest-lived data (price when present).
    entity_ttl = price_ttl if "price" in fields else static_ttl

    return ProductEntity(
        entity_id=str(uuid.uuid4()),
        fields=fields,
        extracted_at=now.isoformat(),
        ttl_expires_at=entity_ttl,
    )


def _heuristic_fallback_extract(content: str, url: str) -> list[_RawExtraction]:
    """Fallback extraction using regex if LLM provider fails."""
    import re
    extractions = []
    
    # Try finding price (e.g. ₹59,999, Rs. 59999, 59990)
    prices = re.findall(r"(?:₹|Rs\.?|INR)\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)", content, re.IGNORECASE)
    price_val = None
    if prices:
        try:
            price_val = float(prices[0].replace(",", ""))
        except ValueError:
            price_val = None

    # Extract bullet points/specs
    specs = [line.strip("- •*").strip() for line in content.split("\n") if line.strip().startswith(("-", "•", "*")) and len(line.strip()) > 5][:5]

    if price_val is None and not specs:
        return []

    # Try finding product title
    first_line = content.split("\n")[0].strip()
    title = first_line[:80] if len(first_line) > 5 else "Product"

    extractions.append(_RawExtraction(name=title, price=price_val, specs=specs))
    return extractions



from concurrent.futures import ThreadPoolExecutor, as_completed


def _extract_single_result(chain: Runnable, fallback_chain: Runnable | None, result: TavilySearchResult) -> list[ProductEntity]:
    cleaned_content = sanitize_content(result.content)[:3500]
    snippet = cleaned_content[:200]
    extractions = None

    # Approach 1: Primary provider extraction
    try:
        raw = chain.invoke(
            {"content": cleaned_content},
            config={
                "callbacks": [get_langfuse_handler()],
            },
        )
        if isinstance(raw, _RawExtractionBatch):
            extractions = raw.products
        elif isinstance(raw, list):
            extractions = raw
        elif isinstance(raw, _RawExtraction):
            extractions = [raw]
    except Exception:
        logger.warning(
            "Primary LLM Extraction failed or timed out for %s, trying fallback provider",
            result.url,
        )

    # Approach 2: Fallback provider extraction
    if extractions is None and fallback_chain is not None:
        try:
            raw = fallback_chain.invoke(
                {"content": cleaned_content},
                config={
                    "callbacks": [get_langfuse_handler()],
                },
            )
            if isinstance(raw, _RawExtractionBatch):
                extractions = raw.products
            elif isinstance(raw, list):
                extractions = raw
            elif isinstance(raw, _RawExtraction):
                extractions = [raw]
        except Exception:
            logger.warning(
                "Fallback LLM Extraction failed for %s, using regex heuristic extraction",
                result.url,
            )

    # Approach 3: Deterministic regex/heuristic fallback extraction
    if not extractions:
        extractions = _heuristic_fallback_extract(cleaned_content, result.url)

    # A product detail page is ONE product. Keep a single entity per page to
    # avoid emitting several loosely-named duplicates from one source URL.
    # Prefer an extraction that has a real price; otherwise the first valid one.
    valid = [e for e in extractions if not (e.name is None and e.price is None)]
    if not valid:
        return []
    chosen = next((e for e in valid if e.price is not None and float(e.price) > 0), valid[0])
    return [_build_product_entity(chosen, result.url, snippet, raw_title=result.title)]


@with_provider_retry
def extract_products(
    search_results: list[TavilySearchResult],
) -> list[ProductEntity]:
    if not search_results:
        return []

    chain = build_extractor_chain()
    try:
        fallback_chain = build_extractor_chain(provider_override="groq")
    except Exception:
        fallback_chain = None

    products: list[ProductEntity] = []

    with ThreadPoolExecutor(max_workers=min(4, len(search_results))) as executor:
        futures = [executor.submit(_extract_single_result, chain, fallback_chain, res) for res in search_results]
        for f in as_completed(futures):
            try:
                products.extend(f.result())
            except Exception:
                logger.exception("Failed single product extraction thread")

    return products

