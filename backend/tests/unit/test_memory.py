from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import chromadb
import pytest

from app.retrieval import memory


@pytest.fixture
def memory_collection():
    """Isolated ChromaDB collection with a deterministic embedder.

    The embedder returns the same vector for every text, so any stored entry is
    an exact (similarity 1.0) match for any lookup. Threshold and TTL are what
    the tests actually exercise.
    """
    client = chromadb.EphemeralClient()
    collection_name = "test_query_memory"
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.get_or_create_collection(
        collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    with (
        patch("app.retrieval.memory.get_memory_collection", return_value=collection),
        patch("app.retrieval.memory._embed_text", side_effect=lambda text: [1.0, 0.0, 0.0]),
    ):
        yield collection

    try:
        client.delete_collection(collection_name)
    except Exception:
        pass


def _future_ttl(hours: float = 6.0) -> str:
    return (datetime.now(UTC) + timedelta(hours=hours)).isoformat()


def _past_ttl(hours: float = 1.0) -> str:
    return (datetime.now(UTC) - timedelta(hours=hours)).isoformat()


PAYLOAD = {
    "products": [{"name": "Sony WH-1000XM5", "price": 24999}],
    "synthesis": "Great pick!",
    "metadata": {"iterations": 1},
}


def test_record_then_lookup_returns_payload(memory_collection):
    memory.record_response("wireless earbuds under 3000", PAYLOAD, _future_ttl())

    hit = memory.lookup_response("wireless earbuds under 3000")

    assert hit is not None
    payload, similarity = hit
    assert payload == PAYLOAD
    assert similarity == pytest.approx(1.0, abs=1e-6)


def test_lookup_miss_when_below_threshold(memory_collection):
    memory.record_response("wireless earbuds under 3000", PAYLOAD, _future_ttl())

    # Force the stored entry to look far away from the query.
    with (
        patch.object(memory, "_embed_text", side_effect=lambda text: [1.0, 0.0, 0.0]),
        patch("app.retrieval.memory.get_settings") as mock_settings,
    ):
        # distance 0 -> similarity 1.0; threshold above 1.0 can never be met.
        mock_settings.return_value.memory_similarity_threshold = 1.01
        hit = memory.lookup_response("wireless earbuds under 3000")

    assert hit is None


def test_lookup_miss_when_ttl_expired(memory_collection):
    memory.record_response("wireless earbuds under 3000", PAYLOAD, _past_ttl())

    hit = memory.lookup_response("wireless earbuds under 3000")

    assert hit is None


def test_lookup_miss_when_no_ttl(memory_collection):
    memory.record_response("wireless earbuds under 3000", PAYLOAD, "")

    hit = memory.lookup_response("wireless earbuds under 3000")

    assert hit is None


def test_empty_query_is_never_recorded_or_matched(memory_collection):
    memory.record_response("   ", PAYLOAD, _future_ttl())
    assert memory.lookup_response("   ") is None


def test_normalization_matches_case_and_whitespace(memory_collection):
    memory.record_response("Wireless   Earbuds", PAYLOAD, _future_ttl())

    hit = memory.lookup_response("wireless earbuds")

    assert hit is not None
