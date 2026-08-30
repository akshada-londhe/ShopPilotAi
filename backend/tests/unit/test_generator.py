from unittest.mock import MagicMock, patch

from app.chains.generator import _QueryList, generate_search_queries
from app.models.critic import CriticFeedback
from app.models.query import NormalizedQuery, Budget


def make_query() -> NormalizedQuery:
    return NormalizedQuery(
        intent="purchase",
        category="gaming mouse",
        budget=Budget(
            min=0,
            max=2000,
            currency="INR",
        ),
        constraints=["low latency"],
        preferences=[],
        use_case="gaming",
        confidence_score=0.9,
        assumptions_made=[],
    )


def test_generate_search_queries_returns_list_of_strings():
    with patch("app.chains.generator.build_generator_chain") as mock_build:
        mock_chain = MagicMock()

        mock_chain.invoke.return_value = _QueryList(
            queries=[
                "best gaming mouse under 2000 INR low latency",
                "budget gaming mouse low latency India",
            ]
        )

        mock_build.return_value = mock_chain

        queries = generate_search_queries(make_query())

        assert queries == [
            "best gaming mouse under 2000 INR low latency",
            "budget gaming mouse low latency India",
        ]

        assert isinstance(queries, list)
        assert all(isinstance(query, str) for query in queries)

        mock_chain.invoke.assert_called_once()


def test_generate_search_queries_passes_feedback_when_retrying():
    feedback = CriticFeedback(
        missing_data=["battery life"],
        negative_prompts=["wired mice"],
    )

    with patch("app.chains.generator.build_generator_chain") as mock_build:
        mock_chain = MagicMock()

        mock_chain.invoke.return_value = _QueryList(
            queries=[
                "wireless gaming mouse long battery life under 2000"
            ]
        )

        mock_build.return_value = mock_chain

        queries = generate_search_queries(
            make_query(),
            feedback=feedback,
        )

        assert queries == [
            "wireless gaming mouse long battery life under 2000"
        ]

        mock_chain.invoke.assert_called_once()

        call_args = mock_chain.invoke.call_args.args[0]

        assert call_args["missing_data"] == "battery life"
        assert call_args["negative_prompts"] == "wired mice"
        assert call_args["failed_criteria"] == "none"