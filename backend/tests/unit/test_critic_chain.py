from unittest.mock import MagicMock, patch

from app.chains.critic import critique_results
from app.models.critic import CriticFeedback, CriticVerdict
from app.models.query import Budget, NormalizedQuery


def test_critique_results_returns_verdict():
    query = NormalizedQuery(
        intent="purchase",
        category="earbuds",
        budget=Budget(min=0, max=3000, currency="INR"),
        constraints=["noise cancellation"],
        preferences=[],
        use_case="commute",
        confidence_score=0.9,
    )

    fake_verdict = CriticVerdict(
        relevance=8,
        requirement_match=7,
        evidence_quality=8,
        completeness=7,
        contradiction_flag=False,
        feedback=CriticFeedback(
            missing_data=[],
            negative_prompts=[],
            failed_criteria=[],
        ),
    )

    with patch("app.chains.critic.build_critic_chain") as mock_build:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = fake_verdict
        mock_build.return_value = mock_chain

        verdict = critique_results([], query)

    assert verdict.weighted_score == 7.55
    assert verdict.relevance == 8
    assert verdict.requirement_match == 7
    assert verdict.evidence_quality == 8
    assert verdict.completeness == 7
    assert verdict.contradiction_flag is False
    assert verdict.feedback.missing_data == []
    assert verdict.feedback.negative_prompts == []
    assert verdict.feedback.failed_criteria == []


def test_critique_results_with_no_products_gets_low_scores_via_prompt_context():
    query = NormalizedQuery(
        intent="purchase",
        category="earbuds",
        budget=Budget(min=0, max=3000, currency="INR"),
        constraints=["noise cancellation"],
        preferences=[],
        use_case="commute",
        confidence_score=0.9,
    )

    with patch("app.chains.critic.build_critic_chain") as mock_build:
        mock_chain = MagicMock()
        mock_build.return_value = mock_chain

        critique_results([], query)

        call_args = mock_chain.invoke.call_args
        payload = call_args.args[0]

        assert payload["product_summary"] == "0 products found."
        assert payload["category"] == "earbuds"
        assert payload["budget_max"] == 3000
        assert payload["currency"] == "INR"
        assert payload["constraints"] == "noise cancellation"
        assert payload["preferences"] == "none"
        assert payload["use_case"] == "commute"