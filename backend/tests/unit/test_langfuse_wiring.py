from unittest.mock import MagicMock, patch

from app.chains.normalizer import normalize_query
from app.models.query import Budget, NormalizedQuery


def test_normalize_query_passes_langfuse_callback_to_chain():
    fake_result = NormalizedQuery(
        intent="purchase", category="earbuds", budget=Budget(min=0, max=3000, currency="INR"),
        constraints=[], preferences=[], use_case="commute", confidence_score=0.9,
    )

    with patch("app.chains.normalizer.build_normalizer_chain") as mock_build, \
         patch("app.chains.normalizer.get_langfuse_handler") as mock_handler:

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = fake_result
        mock_build.return_value = mock_chain
        mock_handler.return_value = "fake-handler"

        normalize_query("wireless earbuds under 3000")

        call_kwargs = mock_chain.invoke.call_args
        assert call_kwargs.kwargs.get("config") == {"callbacks": ["fake-handler"]}