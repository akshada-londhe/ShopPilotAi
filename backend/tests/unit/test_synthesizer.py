from unittest.mock import MagicMock, patch

from app.chains.synthesizer import synthesize_answer
from app.models.query import Budget, NormalizedQuery


def test_synthesize_answer_calls_groq_chain_and_returns_text():
    query = NormalizedQuery(
        intent="purchase", category="earbuds", budget=Budget(min=0, max=3000, currency="INR"),
        constraints=["noise cancellation"], preferences=[], use_case="commute", confidence_score=0.9,
    )

    with patch("app.chains.synthesizer.build_synthesizer_chain") as mock_build:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "Based on your requirements, the Sony WF-1000XM4 (Rs 2,999, source: amazon.in) offers noise cancellation within budget."
        mock_build.return_value = mock_chain

        answer = synthesize_answer([], query)

    assert "amazon.in" in answer or len(answer) > 0
    mock_chain.invoke.assert_called_once()


from app.chains.matcher import MatchedProduct
from app.models.product import ExtractedField, ProductEntity


def _matched(entity_id: str, name: str, price: float, url: str, constraints: list[str]) -> MatchedProduct:
    product = ProductEntity(
        entity_id=entity_id,
        fields={
            "name": ExtractedField(value=name, source_url=url, snippet=""),
            "price": ExtractedField(value=price, source_url=url, snippet=""),
            "spec_0": ExtractedField(value="Bluetooth 5.3", source_url=url, snippet=""),
        },
        extracted_at="2026-08-30T10:00:00",
        ttl_expires_at="2099-01-01T00:00:00+00:00",
    )
    return MatchedProduct(product=product, soft_score=8.0, matched_constraints=constraints)


def test_synthesizer_prompt_receives_top_pick_and_alternatives():
    query = NormalizedQuery(
        intent="purchase", category="earbuds", budget=Budget(min=0, max=3000, currency="INR"),
        constraints=["noise cancellation"], preferences=[], use_case="commute", confidence_score=0.9,
    )
    top = _matched("top", "JBL Wave Beam 2", 2999, "https://www.amazon.in/dp/AAAAAAAAAA", ["noise cancellation"])
    alt = _matched("alt", "boAt Rockerz 450", 2199, "https://www.amazon.in/dp/BBBBBBBBBB", [])

    with patch("app.chains.synthesizer.build_synthesizer_chain") as mock_build:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "The JBL Wave Beam 2 (https://www.amazon.in/dp/AAAAAAAAAA) is the best pick, chosen over the boAt Rockerz 450 (https://www.amazon.in/dp/BBBBBBBBBB)."
        mock_build.return_value = mock_chain

        synthesize_answer([top, alt], query)

    payload = mock_chain.invoke.call_args.args[0]
    # The top pick and the alternative must both reach the model, with prices.
    assert "JBL Wave Beam 2" in payload["top_pick"]
    assert "2999" in payload["top_pick"]
    assert "boAt Rockerz 450" in payload["alternatives"]
    assert "2199" in payload["alternatives"]


def test_synthesizer_alternatives_empty_when_single_candidate():
    query = NormalizedQuery(
        intent="purchase", category="earbuds", budget=Budget(min=0, max=3000, currency="INR"),
        constraints=[], preferences=[], use_case="commute", confidence_score=0.9,
    )
    only = _matched("only", "JBL Wave Beam 2", 2999, "https://www.amazon.in/dp/AAAAAAAAAA", [])

    with patch("app.chains.synthesizer.build_synthesizer_chain") as mock_build:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "The JBL Wave Beam 2 fits your needs."
        mock_build.return_value = mock_chain

        synthesize_answer([only], query)

    payload = mock_chain.invoke.call_args.args[0]
    assert "None" in payload["alternatives"]
