import logging
from dataclasses import dataclass
from functools import lru_cache

from tavily import TavilyClient

from app.config import get_settings

logger = logging.getLogger(__name__)

# Spec FR5: rate limit configurable, default 5 calls per pipeline run.
MAX_TAVILY_CALLS_PER_PIPELINE = 5
MAX_SEARCH_RESULTS_PER_PIPELINE = 4


@dataclass
class TavilySearchResult:
    url: str
    content: str
    title: str


@lru_cache
def _get_tavily_client() -> TavilyClient:
    settings = get_settings()
    return TavilyClient(api_key=settings.tavily_api_key)


import re
import urllib.parse


def _is_direct_product_url(url: str) -> bool:
    """Check if a URL points directly to an individual product detail page."""
    lower = url.lower()
    if "amazon.in" in lower:
        return bool(
            "/dp/" in lower
            or "/gp/product/" in lower
            or "/d/" in lower
            or re.search(r"/(?:dp|gp/product|d)/[a-z0-9]{10}", lower)
        ) and not ("/s?" in lower or "/s/" in lower or "/gp/browse" in lower)
    if "flipkart.com" in lower:
        return bool(
            "/p/" in lower
            or "/product/" in lower
            or "pid=" in lower
            or "/itm" in lower
        ) and not ("/search?" in lower or "/pr?sid=" in lower)
    return False


def clean_canonical_url(url: str) -> str:
    """Extract clean canonical URL for Amazon (ASIN) and Flipkart.

    Amazon sponsored-ad results wrap the real product in an /sspa/click
    redirect whose `url=` query param holds the true destination, while an
    ad/tracking ASIN can appear elsewhere in the string. We must resolve to the
    product the card actually describes, so we unwrap that param first and only
    ever read the ASIN from the URL PATH (never query params).
    """
    if not url:
        return url

    if "amazon" in url.lower():
        parsed = urllib.parse.urlparse(url)

        # Unwrap sponsored-ad redirects: the real destination is in `url=`.
        if "/sspa/click" in parsed.path.lower() or "/gp/slredirect" in parsed.path.lower():
            wrapped = urllib.parse.parse_qs(parsed.query).get("url", [None])[0]
            if wrapped:
                target = urllib.parse.unquote(wrapped)
                # target is a site-relative path like /Brand-Model/dp/ASIN/...
                asin = re.search(r"/(?:dp|gp/product|d)/([A-Z0-9]{10})", target, re.IGNORECASE)
                if asin:
                    return f"https://www.amazon.in/dp/{asin.group(1).upper()}"

        # Read the ASIN from the PATH only, so a tracking ASIN sitting in a
        # query param can never be mistaken for the product.
        asin_match = re.search(r"/(?:dp|gp/product|d)/([A-Z0-9]{10})", parsed.path, re.IGNORECASE)
        if asin_match:
            return f"https://www.amazon.in/dp/{asin_match.group(1).upper()}"

    # Clean Flipkart URLs
    if "flipkart.com" in url.lower():
        base = url.split("?")[0]
        pid_match = re.search(r"pid=([A-Z0-9]+)", url, re.IGNORECASE)
        if pid_match:
            return f"{base}?pid={pid_match.group(1)}"
        return base

    return url


def _search_single_query(client: TavilyClient, query: str, max_results: int) -> list[dict]:
    """Execute a search query with targeted domains first, then broad search fallback."""
    # Approach 1: Targeted domain search
    try:
        res = client.search(
            query=query,
            max_results=max_results,
            include_domains=["amazon.in", "flipkart.com"],
        )
        items = res.get("results", [])
        if items:
            return items
    except Exception:
        logger.warning("Targeted domain Tavily search failed for: %s, trying broad search", query)

    # Approach 2: Broad e-commerce search fallback
    try:
        res = client.search(
            query=f"{query} buy india price",
            max_results=max_results,
        )
        return res.get("results", [])
    except Exception:
        logger.exception("Broad Tavily search fallback failed for: %s", query)
        return []


def search_products(
    queries: list[str], max_results_per_query: int = 5
) -> list[TavilySearchResult]:
    """Search Tavily for each query with multi-approach retry fallback."""
    client = _get_tavily_client()
    truncated_queries = queries[:MAX_TAVILY_CALLS_PER_PIPELINE]
    seen_urls: set[str] = set()
    direct_results: list[TavilySearchResult] = []
    other_results: list[TavilySearchResult] = []

    for query in truncated_queries:
        results = _search_single_query(client, query, max_results_per_query)

        for item in results:
            raw_url = item.get("url", "")
            if not raw_url:
                continue

            canonical_url = clean_canonical_url(raw_url)
            if canonical_url in seen_urls:
                continue

            lower_url = canonical_url.lower()
            seen_urls.add(canonical_url)
            search_item = TavilySearchResult(
                url=canonical_url,
                content=item.get("content", ""),
                title=item.get("title", ""),
            )

            if _is_direct_product_url(canonical_url):
                direct_results.append(search_item)
            elif not ("/s?" in lower_url or "/search?" in lower_url or "/gp/browse" in lower_url):
                other_results.append(search_item)

    # Return direct product URLs first, then other valid store pages
    combined = direct_results + other_results
    return combined[:MAX_SEARCH_RESULTS_PER_PIPELINE]


