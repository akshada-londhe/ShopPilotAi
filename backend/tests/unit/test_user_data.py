from unittest.mock import patch

import chromadb
import pytest

from app import user_data


@pytest.fixture
def saved_collection():
    """Isolated ChromaDB collection standing in for saved_items."""
    client = chromadb.EphemeralClient()
    name = "test_saved_items"
    collection = client.get_or_create_collection(name, metadata={"hnsw:space": "cosine"})

    def _get_collection(_name: str):
        return collection

    with patch("app.user_data._get_collection", side_effect=_get_collection):
        yield collection

    try:
        client.delete_collection(name)
    except Exception:
        pass


USER = "user-123"


def test_two_products_sharing_a_url_both_persist(saved_collection):
    """Regression: saving two different products that share a source URL used
    to collapse to one (doc_id keyed on url alone). Both must now survive."""
    user_data.save_item(USER, "Product A", price=100, link="https://amazon.in/dp/SAMEURL0001")
    user_data.save_item(USER, "Product B", price=200, link="https://amazon.in/dp/SAMEURL0001")

    saved = user_data.get_saved(USER)
    names = {s["name"] for s in saved}
    assert names == {"Product A", "Product B"}


def test_resaving_identical_product_is_idempotent(saved_collection):
    user_data.save_item(USER, "Product A", price=100, link="https://amazon.in/dp/SAMEURL0001")
    user_data.save_item(USER, "Product A", price=100, link="https://amazon.in/dp/SAMEURL0001")

    saved = user_data.get_saved(USER)
    assert [s["name"] for s in saved] == ["Product A"]


def test_two_priceless_products_with_no_url_both_persist(saved_collection):
    user_data.save_item(USER, "Product C", link="")
    user_data.save_item(USER, "Product D", link="")

    names = {s["name"] for s in user_data.get_saved(USER)}
    assert names == {"Product C", "Product D"}


def test_unsave_removes_the_matching_product_only(saved_collection):
    url = "https://amazon.in/dp/SAMEURL0001"
    user_data.save_item(USER, "Product A", price=100, link=url)
    user_data.save_item(USER, "Product B", price=200, link=url)

    removed = user_data.unsave_item(USER, "Product A", link=url)
    assert removed is True

    names = {s["name"] for s in user_data.get_saved(USER)}
    assert names == {"Product B"}
