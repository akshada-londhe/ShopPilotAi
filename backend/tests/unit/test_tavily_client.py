from unittest.mock import MagicMock, patch

from app.retrieval.tavily_client import TavilySearchResult, search_products


def test_search_products_returns_results_from_multiple_queries():
    fake_response = {
        "results": [
            {
                "url": "https://amazon.in/product/1",
                "content": "Logitech G502 gaming mouse, price 1899",
                "title": "Logitech G502",
            }
        ]
    }

    with patch("app.retrieval.tavily_client._get_tavily_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.search.return_value = fake_response
        mock_get_client.return_value = mock_client

        results = search_products(["gaming mouse under 2000"])

    assert len(results) == 1
    assert isinstance(results[0], TavilySearchResult)
    assert results[0].url == "https://amazon.in/product/1"


def test_search_products_deduplicates_urls_across_queries():
    fake_response = {
        "results": [
            {"url": "https://amazon.in/product/1", "content": "Mouse A", "title": "A"},
        ]
    }

    with patch("app.retrieval.tavily_client._get_tavily_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.search.return_value = fake_response
        mock_get_client.return_value = mock_client

        # two queries, both "return" the same URL - should be deduplicated
        results = search_products(["query one", "query two"])

    assert len(results) == 1


def test_search_products_returns_empty_list_on_tavily_failure():
    with patch("app.retrieval.tavily_client._get_tavily_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.search.side_effect = Exception("Tavily API down")
        mock_get_client.return_value = mock_client

        results = search_products(["gaming mouse under 2000"])

    assert results == []


from app.retrieval.tavily_client import clean_canonical_url


def test_clean_canonical_url_plain_amazon_dp():
    url = "https://www.amazon.in/boat-Rockerz-450/dp/B08TVFXP2Z/ref=sr_1_3"
    assert clean_canonical_url(url) == "https://www.amazon.in/dp/B08TVFXP2Z"


def test_clean_canonical_url_sspa_click_uses_real_target_not_ad_asin():
    """Amazon sponsored-ad redirect: the REAL product sits in the url= param,
    while an ad/tracking ASIN may appear earlier in the string. The canonical
    URL must resolve to the real product the card describes, not the ad slot.
    """
    url = (
        "https://www.amazon.in/sspa/click?ie=UTF8&spc=ADSLOT12345"
        "&url=%2FAnker-Soundcore%2Fdp%2FB07NM3RSRQ%2Fref%3Dsr"
    )
    assert clean_canonical_url(url) == "https://www.amazon.in/dp/B07NM3RSRQ"


def test_clean_canonical_url_ignores_asin_in_query_params():
    """An ASIN appearing only in a tracking query param must never be chosen
    over the ASIN in the real product path."""
    url = "https://www.amazon.in/JBL-Tune/dp/B0818LTZVH/ref=x?pd_rd=B0TRACKING1"
    assert clean_canonical_url(url) == "https://www.amazon.in/dp/B0818LTZVH"
