from app.models.critic import CriticFeedback, CriticVerdict


def test_critic_verdict_computes_weighted_score():
    verdict = CriticVerdict(
        relevance=8,
        requirement_match=7,
        evidence_quality=8,
        completeness=7,
        contradiction_flag=False,
        feedback=CriticFeedback(),
    )
    # 0.3*8 + 0.3*7 + 0.25*8 + 0.15*7 = 2.4 + 2.1 + 2.0 + 1.05 = 7.55
    assert verdict.weighted_score == 7.55
    assert verdict.passed is True


def test_critic_verdict_fails_on_contradiction_even_with_high_scores():
    verdict = CriticVerdict(
        relevance=10,
        requirement_match=10,
        evidence_quality=10,
        completeness=10,
        contradiction_flag=True,
        feedback=CriticFeedback(),
    )
    assert verdict.passed is False


def test_critic_verdict_fails_below_threshold():
    verdict = CriticVerdict(
        relevance=5,
        requirement_match=5,
        evidence_quality=5,
        completeness=5,
        contradiction_flag=False,
        feedback=CriticFeedback(),
    )
    assert verdict.weighted_score == 5.0
    assert verdict.passed is False