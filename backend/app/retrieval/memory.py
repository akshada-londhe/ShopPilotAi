"""Semantic memory cache: full-response RAG recall.

A higher, query-level cache in front of the product-level cache in cache.py.
When a search finishes, the complete finished response payload (products,
synthesis, verdict/metadata) is embedded by its raw query string and stored in
its own ChromaDB collection. When the same (or near-identical) query runs
again, the stored payload is served from memory, skipping Tavily and the whole
pipeline. Staleness is bounded by the shortest per-field TTL of the products in
the stored response, so memory never serves stale data.
"""

import hashlib
import json
import logging
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

import chromadb
from chromadb import Collection
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from app.config import get_settings

logger = logging.getLogger(__name__)

# Separate collection from the product-level cache (`products`).
COLLECTION_NAME = "query_memory"


@lru_cache
def _get_embedder() -> DefaultEmbeddingFunction:
    return DefaultEmbeddingFunction()


@lru_cache
def _get_client() -> chromadb.ClientAPI:
    settings = get_settings()
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)


def get_memory_collection() -> Collection:
    client = _get_client()
    return client.get_or_create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _embed_text(text: str) -> list[float]:
    return [float(value) for value in _get_embedder()([text])[0]]


def _normalize_query(query: str) -> str:
    """Recall matches on what the user typed (decision A). Normalize only
    casing/whitespace so trivial differences still hit the same memory entry."""
    return " ".join(query.strip().lower().split())


def _query_id(normalized_query: str) -> str:
    return hashlib.sha256(normalized_query.encode("utf-8")).hexdigest()


def _ttl_is_future(ttl_str: str | None) -> bool:
    if not ttl_str:
        return False
    try:
        ttl = datetime.fromisoformat(ttl_str)
    except ValueError:
        return False
    if ttl.tzinfo is None:
        ttl = ttl.replace(tzinfo=UTC)
    return ttl > datetime.now(UTC)


def record_response(query: str, payload: dict[str, Any], ttl_expires_at: str) -> None:
    """Store a finished response payload keyed by the normalized query.

    ttl_expires_at is the shortest per-field TTL of the products in the
    response (price = 6h dominates), so freshness matches the data inside.
    Failures are logged and swallowed: recording is best-effort and must never
    break the request that produced the result.
    """
    normalized = _normalize_query(query)
    if not normalized:
        return
    try:
        collection = get_memory_collection()
    except Exception:
        logger.exception("ChromaDB memory collection unavailable, skipping record")
        return
    try:
        embedding = _embed_text(normalized)
        collection.upsert(
            ids=[_query_id(normalized)],
            embeddings=[embedding],
            documents=[normalized],
            metadatas=[
                {
                    "query": normalized,
                    "response_json": json.dumps(payload),
                    "created_at": datetime.now(UTC).isoformat(),
                    "ttl_expires_at": ttl_expires_at or "",
                }
            ],
        )
    except Exception:
        logger.exception("Failed to record response to query memory")


def lookup_response(query: str) -> tuple[dict[str, Any], float] | None:
    """Return (payload, similarity) when a fresh stored response matches the
    query at cosine similarity >= the configured threshold, else None.

    A stored response that is stale (its TTL has passed) is treated as a miss
    so the pipeline re-runs live and overwrites it. Any ChromaDB error is a
    graceful miss (pipeline runs as today).
    """
    normalized = _normalize_query(query)
    if not normalized:
        return None
    try:
        collection = get_memory_collection()
    except Exception:
        logger.exception("ChromaDB memory collection unavailable, treating as miss")
        return None
    try:
        embedding = _embed_text(normalized)
        raw = collection.query(query_embeddings=[embedding], n_results=1)
    except Exception:
        logger.exception("Query memory lookup failed, treating as miss")
        return None

    if not raw.get("ids") or not raw["ids"][0]:
        return None

    distance = raw["distances"][0][0]
    metadata = raw["metadatas"][0][0]
    similarity = 1.0 - float(distance)

    threshold = get_settings().memory_similarity_threshold
    if similarity < threshold:
        return None

    if not _ttl_is_future(metadata.get("ttl_expires_at")):
        # Stale stored response: miss, let the pipeline re-run and overwrite.
        return None

    try:
        payload = json.loads(metadata["response_json"])
    except (KeyError, json.JSONDecodeError):
        logger.exception("Stored response payload malformed, treating as miss")
        return None

    return payload, similarity
