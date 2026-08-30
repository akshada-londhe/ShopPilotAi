from unittest.mock import MagicMock, patch

from app.chains.matcher import match_products
from app.models.product import ExtractedField, ProductEntity
from app.models.query import Budget, NormalizedQuery


def make_product(entity_id: str, price: float, specs: list[str]) -> ProductEntity:
    fields = {
        "name": ExtractedField(value=f"Product {entity_id}", source_url="https://x.com", snippet=""),
        "price": ExtractedField(value=price, source_url="https://x.com", snippet=""),
    }
    for i, spec in enumerate(specs):
        fields[f"spec_{i}"] = ExtractedField(value=spec, source_url="https://x.com", snippet="")
    return ProductEntity(
        entity_id=entity_id, fields=fields, extracted_at="2026-08-21T10:00:00",
        ttl_expires_at="2026-08-21T16:00:00",
    )


def make_query(budget_max: int, constraints: list[str]) -> NormalizedQuery:
    return NormalizedQuery(
        intent="purchase", category="mouse", budget=Budget(min=0, max=budget_max, currency="INR"),
        constraints=constraints, preferences=[], use_case="gaming", confidence_score=0.9,
    )


def test_over_budget_products_are_excluded_without_llm_call():
    cheap = make_product("1", price=1500, specs=["low latency"])
    expensive = make_product("2", price=5000, specs=["low latency"])
    query = make_query(budget_max=2000, constraints=["low latency"])

    with patch("app.chains.matcher.build_matcher_chain") as mock_build:
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = {"score": 8}
        mock_build.return_value = mock_chain

        results = match_products([cheap, expensive], query)

    result_ids = [r.product.entity_id for r in results]
    assert "1" in result_ids
    assert "2" not in result_ids  # excluded by programmatic budget check


def test_no_preferences_skips_llm_call_entirely():
    product = make_product("1", price=1500, specs=["low latency"])
    query = make_query(budget_max=2000, constraints=["low latency"])
    # no soft preferences on this query, only hard constraints -> Phase 2 has nothing to score

    with patch("app.chains.matcher.build_matcher_chain") as mock_build:
        results = match_products([product], query)

    assert len(results) == 1
    mock_build.assert_not_called()


def _entity(entity_id: str, name: str, raw_title: str | None, price: float | None,
            source_url: str = "https://www.amazon.in/dp/B0CV7CKT55") -> ProductEntity:
    fields = {
        "name": ExtractedField(value=name, source_url=source_url, snippet=""),
    }
    if raw_title is not None:
        fields["raw_title"] = ExtractedField(value=raw_title, source_url=source_url, snippet="")
    if price is not None:
        fields["price"] = ExtractedField(value=price, source_url=source_url, snippet="")
    return ProductEntity(
        entity_id=entity_id, fields=fields, extracted_at="2026-08-30T10:00:00",
        ttl_expires_at="2099-01-01T00:00:00+00:00",
    )


def _phone_query(budget_max: int = 10000000) -> NormalizedQuery:
    return NormalizedQuery(
        intent="purchase", category="phone",
        budget=Budget(min=0, max=budget_max, currency="INR"),
        constraints=["redmi 13c"], preferences=[], use_case="daily", confidence_score=0.9,
    )


def test_accessory_filtered_from_raw_title_even_when_name_is_clean():
    """Regression: name-cleaning turned a case listing into 'Redmi 13C 5G'.
    The raw_title still says 'Back Cover ... Case', so it must be filtered when
    the buyer asked for a phone."""
    case = _entity(
        "case",
        name="Redmi 13C 5G",  # cleaned name hides that it's a case
        raw_title="Pikkme Redmi 13C 5G Back Cover Camera Protection Shockproof Soft Matte Silicone Back Case for Redmi 13C 5G (Purple)",
        price=199,
    )
    with patch("app.chains.matcher.build_matcher_chain"):
        results = match_products([case], _phone_query())
    assert results == []  # the accessory was excluded


def test_real_phone_passes_when_asked_for_phone():
    phone = _entity(
        "phone",
        name="Redmi 13C 5G",
        raw_title="Redmi 13C 5G (Starfrost White, 4GB RAM, 128GB Storage)",
        price=10999,
    )
    with patch("app.chains.matcher.build_matcher_chain"):
        results = match_products([phone], _phone_query())
    assert [r.product.entity_id for r in results] == ["phone"]


def test_phone_case_query_still_returns_cases():
    """When the buyer explicitly wants a case, the accessory filter must stay off."""
    case = _entity(
        "case",
        name="Pikkme Redmi 13C Back Cover",
        raw_title="Pikkme Redmi 13C 5G Back Cover Silicone Case (Purple)",
        price=199,
    )
    query = NormalizedQuery(
        intent="purchase", category="phone case",
        budget=Budget(min=0, max=1000, currency="INR"),
        constraints=[], preferences=[], use_case="protection", confidence_score=0.9,
    )
    with patch("app.chains.matcher.build_matcher_chain"):
        results = match_products([case], query)
    assert [r.product.entity_id for r in results] == ["case"]


def test_priced_product_preferred_over_priceless_so_best_match_has_price():
    priced = _entity("priced", name="Redmi 13C 5G", raw_title="Redmi 13C 5G Phone",
                     price=10999, source_url="https://www.amazon.in/dp/AAAAAAAAAA")
    priceless = _entity("priceless", name="Redmi 13C 5G", raw_title="Redmi 13C 5G Phone",
                        price=None, source_url="https://www.amazon.in/dp/BBBBBBBBBB")
    with patch("app.chains.matcher.build_matcher_chain"):
        results = match_products([priceless, priced], _phone_query())
    assert results, "expected at least one match"
    # Best match must carry a real price whenever any priced candidate exists.
    assert results[0].product.get_price() is not None
    assert "priceless" not in [r.product.entity_id for r in results]
