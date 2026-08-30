from unittest.mock import patch

import pytest

from app.models.product import ExtractedField, ProductEntity
from app.models.query import Budget, NormalizedQuery
from app.graph.retry_loop import run_pipeline


def make_query() -> NormalizedQuery:
    return NormalizedQuery(
        intent="purchase",
        category="earbuds",
        budget=Budget(
            min=0,
            max=3000,
            currency="INR",
        ),
        constraints=["noise cancellation"],
        preferences=[],
        use_case="commute",
        confidence_score=0.9,
    )


def make_products() -> list[ProductEntity]:
    return [
        ProductEntity(
            entity_id=f"product_{i}",
            fields={
                "name": ExtractedField(
                    value=f"Test Earbuds {i}",
                    source_url="https://example.com",
                    snippet="Test product",
                ),
                "price": ExtractedField(
                    value=2500,
                    source_url="https://example.com",
                    snippet="Test price",
                ),
            },
            extracted_at="2026-08-24T10:00:00+00:00",
            ttl_expires_at="2099-08-24T10:00:00+00:00",
        )
        for i in range(3)
    ]


@pytest.mark.integration
def test_second_identical_query_hits_cache_and_skips_tavily():
    """
    Verify that a sufficient cache result prevents a live Tavily search.

    Groq and Tavily are mocked because this test is specifically testing
    the cache/pipeline integration, not external API availability.
    """

    query = make_query()
    products = make_products()

    with (
        patch(
            "app.graph.retry_loop.generate_search_queries",
            return_value=["wireless earbuds under 3000"],
        ),
        patch(
            "app.graph.retry_loop.check_cache_sufficiency",
            side_effect=[
                [],
                products,
            ],
        ) as mock_cache,
        patch(
            "app.graph.retry_loop.search_products",
            return_value=[],
        ) as mock_search,
        patch(
            "app.graph.retry_loop.extract_products",
            return_value=products,
        ) as mock_extract,
        patch(
            "app.graph.retry_loop.persist_products",
        ) as mock_persist,
        patch(
            "app.graph.retry_loop.match_products",
            return_value=[],
        ),
        patch(
            "app.graph.retry_loop.critique_results",
        ),
        patch(
            "app.graph.retry_loop.synthesize_answer",
            return_value="Test answer",
        ),
    ):
        # First pipeline execution:
        # cache is empty -> Tavily should be called.
        run_pipeline(query)

        # Second pipeline execution:
        # cache is sufficient -> Tavily should NOT be called.
        run_pipeline(query)

    assert mock_cache.call_count == 2

    # Tavily should only have been called during the first execution.
    mock_search.assert_called_once()

    # Products were extracted from the first live search.
    mock_extract.assert_called_once()

    # Products were persisted after the first live search.
    mock_persist.assert_called_once()
