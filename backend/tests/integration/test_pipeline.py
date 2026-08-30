"""
Integration test: makes REAL calls to Groq and Tavily.
Requires a valid backend/.env with both API keys set.
Run manually, not on every commit (see spec Testing Strategy, Layer 2).
"""

import pytest

from app.chains.normalizer import normalize_query
from app.graph.retry_loop import run_pipeline


@pytest.mark.integration
def test_full_pipeline_wireless_earbuds_query():
    normalized = normalize_query(
        "best wireless earbuds under 3000 rupees with noise cancellation"
    )

    assert normalized.category.lower() in ("earbuds", "wireless earbuds", "headphones")
    assert normalized.budget.max <= 3000
    assert normalized.confidence_score >= 0.6  # should be a clear, unambiguous query

    result = run_pipeline(normalized)

    assert result.iterations >= 1
    assert result.iterations <= 3
    assert result.verdict is not None

    # Either it passed and produced a synthesis, or it's an honest best-available.
    if not result.is_best_available:
        assert result.synthesis is not None
        assert len(result.synthesis) > 0
    else:
        assert result.synthesis is None

    # Every matched product must carry source URLs (spec: source-linked evidence).
    for m in result.matched:
        for extracted_field in m.product.fields.values():
            assert extracted_field.source_url.startswith("http")
