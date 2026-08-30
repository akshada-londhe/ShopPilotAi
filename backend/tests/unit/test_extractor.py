from unittest.mock import MagicMock, patch

from app.chains.extractor import _RawExtraction, _RawExtractionBatch, extract_products
from app.retrieval.tavily_client import TavilySearchResult


def test_extract_products_returns_product_entities():
    search_result = TavilySearchResult(
        url="https://amazon.in/product/1",
        content="Logitech G502 Hero gaming mouse. Price: Rs 1,899. 25600 DPI sensor.",
        title="Logitech G502 Hero",
    )

    fake_extraction = _RawExtraction(
        name="Logitech G502 Hero",
        price=1899,
        specs=["25600 DPI sensor"],
    )

    with patch("app.chains.extractor.build_extractor_chain") as mock_build:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = fake_extraction
        mock_build.return_value = mock_chain

        products = extract_products([search_result])

    assert len(products) == 1
    assert products[0].get_name() == "Logitech G502 Hero"
    assert products[0].get_price() == 1899
    assert products[0].fields["price"].source_url == "https://amazon.in/product/1"


def test_extract_products_skips_result_on_extraction_failure():
    search_result = TavilySearchResult(
        url="https://x.com/1",
        content="garbage",
        title="x",
    )

    with patch("app.chains.extractor.build_extractor_chain") as mock_build:
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = Exception("extraction failed")
        mock_build.return_value = mock_chain

        products = extract_products([search_result])

    assert products == []


def test_extract_products_keeps_one_product_per_page():
    """A product detail page is one product. If the LLM returns several, keep a
    single entity (prefer one with a real price) to avoid duplicates per source."""
    search_result = TavilySearchResult(
        url="https://example.com/products",
        content="One primary product with price and specs.",
        title="Products",
    )

    with patch("app.chains.extractor.build_extractor_chain") as mock_build:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = _RawExtractionBatch(
            products=[
                _RawExtraction(name="Product A", price=None, specs=["spec A"]),
                _RawExtraction(name="Product B", price=200, specs=["spec B"]),
            ]
        )
        mock_build.return_value = mock_chain

        products = extract_products([search_result])

    # Exactly one product, and the priced one is preferred.
    assert len(products) == 1
    assert products[0].get_name() == "Product B"
    assert products[0].get_price() == 200
