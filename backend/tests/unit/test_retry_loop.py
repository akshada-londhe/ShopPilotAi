from unittest.mock import patch

from app.graph.retry_loop import run_pipeline
from app.models.critic import CriticFeedback, CriticVerdict
from app.models.query import Budget, NormalizedQuery


def make_query() -> NormalizedQuery:
    return NormalizedQuery(
        intent="purchase",
        category="earbuds",
        budget=Budget(min=0, max=3000, currency="INR"),
        constraints=["noise cancellation"],
        preferences=[],
        use_case="commute",
        confidence_score=0.9,
    )


def passing_verdict() -> CriticVerdict:
    return CriticVerdict(
        relevance=8,
        requirement_match=8,
        evidence_quality=8,
        completeness=8,
        contradiction_flag=False,
        feedback=CriticFeedback(),
    )


def failing_verdict() -> CriticVerdict:
    return CriticVerdict(
        relevance=3,
        requirement_match=3,
        evidence_quality=3,
        completeness=3,
        contradiction_flag=False,
        feedback=CriticFeedback(
            missing_data=["battery life"]
        ),
    )


@patch("app.graph.retry_loop.synthesize_answer", return_value="Great pick!")
@patch(
    "app.graph.retry_loop.critique_results",
    return_value=passing_verdict(),
)
@patch("app.graph.retry_loop.match_products", return_value=[])
@patch("app.graph.retry_loop.extract_products", return_value=[])
@patch("app.graph.retry_loop.search_products", return_value=[])
@patch(
    "app.graph.retry_loop.generate_search_queries",
    return_value=["earbuds under 3000"],
)
def test_pipeline_passes_on_first_try(
    mock_gen,
    mock_search,
    mock_extract,
    mock_match,
    mock_critique,
    mock_synth,
):
    result = run_pipeline(make_query())

    assert result.iterations == 1
    assert result.is_best_available is False
    assert result.synthesis == "Great pick!"
    mock_critique.assert_called_once()


@patch("app.graph.retry_loop.synthesize_answer")
@patch("app.graph.retry_loop.critique_results")
@patch("app.graph.retry_loop.match_products", return_value=[])
@patch("app.graph.retry_loop.extract_products", return_value=[])
@patch("app.graph.retry_loop.search_products", return_value=[])
@patch(
    "app.graph.retry_loop.generate_search_queries",
    return_value=["query"],
)
def test_pipeline_retries_then_passes(
    mock_gen,
    mock_search,
    mock_extract,
    mock_match,
    mock_critique,
    mock_synth,
):
    mock_critique.side_effect = [
        failing_verdict(),
        passing_verdict(),
    ]

    mock_synth.return_value = "Found it on retry!"

    result = run_pipeline(make_query())

    assert result.iterations == 2
    assert result.is_best_available is False
    assert result.synthesis == "Found it on retry!"
    assert mock_critique.call_count == 2


@patch("app.graph.retry_loop.synthesize_answer")
@patch("app.graph.retry_loop.critique_results")
@patch("app.graph.retry_loop.match_products", return_value=[])
@patch("app.graph.retry_loop.extract_products", return_value=[])
@patch("app.graph.retry_loop.search_products", return_value=[])
@patch(
    "app.graph.retry_loop.generate_search_queries",
    return_value=["query"],
)
def test_pipeline_stops_at_max_iterations_and_returns_best_available(
    mock_gen,
    mock_search,
    mock_extract,
    mock_match,
    mock_critique,
    mock_synth,
):
    verdict_1 = CriticVerdict(
        relevance=3,
        requirement_match=3,
        evidence_quality=3,
        completeness=3,
        contradiction_flag=False,
        feedback=CriticFeedback(
            missing_data=["battery life"]
        ),
    )

    verdict_2 = CriticVerdict(
        relevance=4,
        requirement_match=4,
        evidence_quality=4,
        completeness=4,
        contradiction_flag=False,
        feedback=CriticFeedback(
            missing_data=["battery life"]
        ),
    )

    verdict_3 = CriticVerdict(
        relevance=5,
        requirement_match=5,
        evidence_quality=5,
        completeness=5,
        contradiction_flag=False,
        feedback=CriticFeedback(
            missing_data=["battery life"]
        ),
    )

    mock_critique.side_effect = [
        verdict_1,
        verdict_2,
        verdict_3,
    ]

    result = run_pipeline(make_query())

    assert result.iterations == 3
    assert result.is_best_available is True
    assert result.synthesis is None
    assert result.verdict.weighted_score == verdict_3.weighted_score
    assert mock_critique.call_count == 3
    mock_synth.assert_not_called()


@patch("app.graph.retry_loop.synthesize_answer")
@patch("app.graph.retry_loop.critique_results")
@patch("app.graph.retry_loop.match_products", return_value=[])
@patch("app.graph.retry_loop.extract_products", return_value=[])
@patch("app.graph.retry_loop.search_products", return_value=[])
@patch(
    "app.graph.retry_loop.generate_search_queries",
    return_value=["query"],
)
def test_pipeline_stops_early_on_plateau(
    mock_gen,
    mock_search,
    mock_extract,
    mock_match,
    mock_critique,
    mock_synth,
):
    stuck_verdict_1 = CriticVerdict(
        relevance=5,
        requirement_match=5,
        evidence_quality=5,
        completeness=5,
        contradiction_flag=False,
        feedback=CriticFeedback(),
    )

    stuck_verdict_2 = CriticVerdict(
        relevance=5,
        requirement_match=5,
        evidence_quality=5,
        completeness=5,
        contradiction_flag=False,
        feedback=CriticFeedback(),
    )

    mock_critique.side_effect = [
        stuck_verdict_1,
        stuck_verdict_2,
    ]

    result = run_pipeline(make_query())

    assert result.iterations == 2
    assert result.is_best_available is True
    assert result.synthesis is None
    assert mock_critique.call_count == 2
    mock_synth.assert_not_called()


# ---------------------------------------------------------------------------
# CACHE BEHAVIOR TESTS
# ---------------------------------------------------------------------------


@patch("app.graph.retry_loop.persist_products")
@patch(
    "app.graph.retry_loop.synthesize_answer",
    return_value="Cached pick!",
)
@patch("app.graph.retry_loop.critique_results")
@patch("app.graph.retry_loop.match_products")
@patch("app.graph.retry_loop.extract_products")
@patch("app.graph.retry_loop.search_products")
@patch("app.graph.retry_loop.check_cache_sufficiency")
@patch(
    "app.graph.retry_loop.generate_search_queries",
    return_value=["earbuds under 3000"],
)
def test_pipeline_skips_tavily_when_cache_is_sufficient(
    mock_gen,
    mock_cache_check,
    mock_search,
    mock_extract,
    mock_match,
    mock_critique,
    mock_synth,
    mock_persist,
):
    from app.models.product import ExtractedField, ProductEntity

    cached_products = [
        ProductEntity(
            entity_id="cached_1",
            fields={
                "name": ExtractedField(
                    value="Cached Earbuds",
                    source_url="https://x.com",
                    snippet="",
                )
            },
            extracted_at="2026-08-21T08:00:00+00:00",
            ttl_expires_at="2026-08-21T14:00:00+00:00",
        )
    ]

    mock_cache_check.return_value = cached_products
    mock_match.return_value = []
    mock_critique.return_value = passing_verdict()

    run_pipeline(make_query())

    mock_search.assert_not_called()
    mock_extract.assert_not_called()

    mock_match.assert_called_once_with(
        cached_products,
        make_query(),
    )

    mock_persist.assert_not_called()


@patch("app.graph.retry_loop.persist_products")
@patch(
    "app.graph.retry_loop.synthesize_answer",
    return_value="Live search pick!",
)
@patch("app.graph.retry_loop.critique_results")
@patch("app.graph.retry_loop.match_products", return_value=[])
@patch("app.graph.retry_loop.extract_products", return_value=[])
@patch("app.graph.retry_loop.search_products", return_value=[])
@patch(
    "app.graph.retry_loop.check_cache_sufficiency",
    return_value=[],
)
@patch(
    "app.graph.retry_loop.generate_search_queries",
    return_value=["earbuds under 3000"],
)
def test_pipeline_falls_back_to_tavily_when_cache_insufficient(
    mock_gen,
    mock_cache_check,
    mock_search,
    mock_extract,
    mock_match,
    mock_critique,
    mock_synth,
    mock_persist,
):
    mock_critique.return_value = passing_verdict()

    run_pipeline(make_query())

    mock_search.assert_called_once()
    mock_persist.assert_called_once()