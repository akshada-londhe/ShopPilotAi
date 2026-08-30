from unittest.mock import MagicMock, patch

from app.chains.normalizer import normalize_query
from app.models.query import NormalizedQuery, Budget


def test_normalize_query_returns_normalized_query():
    fake_result = NormalizedQuery(
        intent="purchase",
        category="earbuds",
        budget=Budget(min=0, max=3000, currency="INR"),
        constraints=["noise cancellation"],
        preferences=[],
        use_case="commute",
        confidence_score=0.9,
    )

    with patch("app.chains.normalizer.build_normalizer_chain") as mock_build:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = fake_result
        mock_build.return_value = mock_chain

        result = normalize_query("wireless earbuds under 3000 with noise cancellation")

    assert result.category == "earbuds"
    assert result.budget.max == 3000
    mock_chain.invoke.assert_called_once()