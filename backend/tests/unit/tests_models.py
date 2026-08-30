from app.models.product import ExtractedField, ProductEntity
from app.models.query import Budget, NormalizedQuery


def test_normalized_query_valid():
    q = NormalizedQuery(
        intent="purchase",
        category="earbuds",
        budget=Budget(min=0, max=3000, currency="INR"),
        constraints=["noise cancellation"],
        preferences=["compact"],
        use_case="commute",
        confidence_score=0.88,
    )
    assert q.category == "earbuds"
    assert q.budget.max == 3000
    assert q.confidence_score == 0.88


def test_normalized_query_confidence_out_of_range_rejected():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        NormalizedQuery(
            intent="purchase",
            category="earbuds",
            budget=Budget(min=0, max=3000, currency="INR"),
            constraints=[],
            preferences=[],
            use_case="commute",
            confidence_score=1.5,  # invalid: must be 0-1
        )


def test_product_entity_requires_source_on_fields():
    field = ExtractedField(
        value=1899,
        source_url="https://amazon.in/product/123",
        snippet="Price: Rs 1,899",
    )
    product = ProductEntity(
        entity_id="prod_1",
        fields={"price": field},
        extracted_at="2026-08-21T10:00:00",
        ttl_expires_at="2026-08-21T16:00:00",
    )
    assert product.fields["price"].value == 1899
    assert product.fields["price"].source_url.startswith("https://")