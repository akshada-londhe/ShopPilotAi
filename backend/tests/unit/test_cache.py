from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import chromadb
import pytest

from app.models.product import ExtractedField, ProductEntity
from app.retrieval.cache import check_cache_sufficiency, persist_products


@pytest.fixture
def test_collection():
    """Create a completely isolated ChromaDB collection for each test."""
    client = chromadb.EphemeralClient()

    collection_name = "test_products"

    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    with (
        patch(
            "app.retrieval.cache.get_chroma_collection",
            return_value=collection,
        ),
        patch(
            "app.retrieval.cache._embed_text",
            side_effect=lambda text: [1.0, 0.0, 0.0],
        ),
    ):
        yield collection

    try:
        client.delete_collection(collection_name)
    except Exception:
        pass


def make_fresh_product(
    entity_id: str,
    hours_old: float = 0.0,
) -> ProductEntity:
    now = datetime.now(timezone.utc)
    extracted_at = now - timedelta(hours=hours_old)
    # Price TTL is 6h (spec FR4); freshness is gated per-field.
    price_ttl = (extracted_at + timedelta(hours=6)).isoformat()
    static_ttl = (extracted_at + timedelta(days=30)).isoformat()

    return ProductEntity(
        entity_id=entity_id,
        fields={
            "name": ExtractedField(
                value="Sony WH-1000XM5",
                source_url="https://x.com",
                snippet="",
                ttl_expires_at=static_ttl,
            ),
            "price": ExtractedField(
                value=24999,
                source_url="https://x.com",
                snippet="",
                ttl_expires_at=price_ttl,
            ),
        },
        extracted_at=extracted_at.isoformat(),
        ttl_expires_at=price_ttl,
    )


def test_persist_and_retrieve_fresh_products(test_collection):
    products = [make_fresh_product(f"p{i}") for i in range(3)]

    persist_products(
        products,
        category="headphones",
    )

    results = check_cache_sufficiency(
        "headphones noise cancellation wireless",
        category="headphones",
    )

    assert len(results) == 3


def test_stale_products_are_excluded(test_collection):
    stale = [
        make_fresh_product(
            f"stale_{i}",
            hours_old=10.0,
        )
        for i in range(3)
    ]

    persist_products(
        stale,
        category="headphones",
    )

    results = check_cache_sufficiency(
        "headphones noise cancellation wireless",
        category="headphones",
    )

    assert len(results) == 0


def test_irrelevant_category_is_excluded(test_collection):
    products = [make_fresh_product(f"p{i}") for i in range(3)]

    persist_products(
        products,
        category="headphones",
    )

    results = check_cache_sufficiency(
        "gaming laptop under 80000",
        category="laptop",
    )

    assert len(results) == 0
