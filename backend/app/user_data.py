"""Per-user application data: search history and saved items.

Stored in ChromaDB alongside products and users. Each record is a document in
a dedicated collection, with metadata holding the user_id and a JSON blob of
the record payload. Embeddings are dummy (ANN is not needed here); we filter
by user_id and sort by timestamp in Python.

Records are re-fetchable / non-critical, but they persist on disk so a user's
history and saved list survive restarts (given a persistent CHROMA_PERSIST_DIR).
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

import chromadb
from chromadb import Collection

logger = logging.getLogger(__name__)

HISTORY_COLLECTION = "search_history"
SAVED_COLLECTION = "saved_items"
_EMBED_DIM = 384
_MAX_HISTORY = 100
_MAX_SAVED = 200


@lru_cache
def _get_client() -> chromadb.ClientAPI:
    from app.config import get_settings

    return chromadb.PersistentClient(path=get_settings().chroma_persist_dir)


def _get_collection(name: str) -> Collection:
    return _get_client().get_or_create_collection(
        name, metadata={"hnsw:space": "cosine"}
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dummy_embedding() -> list[float]:
    return [0.0] * _EMBED_DIM


def _sorted_desc(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Newest first by created_at."""
    return sorted(records, key=lambda r: r.get("created_at", ""), reverse=True)


def _read_user_records(collection: Collection, user_id: str) -> list[dict[str, Any]]:
    try:
        raw = collection.get(where={"user_id": user_id})
    except Exception:
        logger.exception("Failed reading records for user %s", user_id)
        return []
    metadatas = raw.get("metadatas") or []
    records: list[dict[str, Any]] = []
    for meta in metadatas:
        blob = meta.get("payload")
        if not blob:
            continue
        try:
            records.append(json.loads(blob))
        except Exception:
            continue
    return records


# ── Search history ────────────────────────────────────────────────────────────
def record_search(
    user_id: str,
    query: str,
    best_match_name: str | None = None,
    best_match_price: float | None = None,
    best_match_url: str | None = None,
) -> None:
    """Append a search to the user's history. Best-effort; never raises."""
    if not user_id or not query.strip():
        return
    try:
        collection = _get_collection(HISTORY_COLLECTION)
    except Exception:
        logger.exception("search_history collection unavailable")
        return

    record = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "query": query.strip(),
        "best_match_name": best_match_name,
        "best_match_price": best_match_price,
        "best_match_url": best_match_url,
        "created_at": _now(),
    }
    try:
        collection.add(
            ids=[record["id"]],
            documents=[query.strip()],
            embeddings=[_dummy_embedding()],
            metadatas=[{"user_id": user_id, "payload": json.dumps(record)}],
        )
    except Exception:
        logger.exception("Failed to record search for user %s", user_id)


def get_history(user_id: str) -> list[dict[str, Any]]:
    if not user_id:
        return []
    try:
        collection = _get_collection(HISTORY_COLLECTION)
    except Exception:
        logger.exception("search_history collection unavailable")
        return []
    return _sorted_desc(_read_user_records(collection, user_id))[:_MAX_HISTORY]


# ── Saved items ────────────────────────────────────────────────────────────────
def _saved_doc_id(user_id: str, name: str, url: str | None) -> str:
    """Stable per-user id so saving the same product twice is idempotent.

    Keyed on BOTH name and url. Keying on url alone collapsed distinct products
    that share a source URL (common on low-quality extractions where the best
    match and its alternatives carry the same or empty URL): the second save
    overwrote the first and silently vanished. name+url matches the frontend's
    `${name}|${link}` key, so two different products persist independently while
    re-saving the identical product stays idempotent.
    """
    key = f"{user_id}|{name.strip().lower()}|{(url or '').strip().lower()}"
    return hashlib.sha256(key.encode()).hexdigest()


def save_item(
    user_id: str,
    name: str,
    price: float | None = None,
    image: str | None = None,
    merchant: str | None = None,
    link: str | None = None,
) -> dict[str, Any]:
    """Save (or upsert) a product for the user. Returns the stored record."""
    if not user_id or not name.strip():
        raise ValueError("user_id and product name are required.")

    collection = _get_collection(SAVED_COLLECTION)
    doc_id = _saved_doc_id(user_id, name, link)
    record = {
        "id": doc_id,
        "user_id": user_id,
        "name": name.strip(),
        "price": price,
        "image": image or "/placeholder-product.svg",
        "merchant": merchant or "",
        "link": link or "",
        "created_at": _now(),
    }
    collection.upsert(
        ids=[doc_id],
        documents=[name.strip()],
        embeddings=[_dummy_embedding()],
        metadatas=[{"user_id": user_id, "payload": json.dumps(record)}],
    )
    return record


def get_saved(user_id: str) -> list[dict[str, Any]]:
    if not user_id:
        return []
    try:
        collection = _get_collection(SAVED_COLLECTION)
    except Exception:
        logger.exception("saved_items collection unavailable")
        return []
    return _sorted_desc(_read_user_records(collection, user_id))[:_MAX_SAVED]


def unsave_item(user_id: str, name: str, link: str | None = None) -> bool:
    """Remove a saved product. Returns True if something was deleted."""
    if not user_id:
        return False
    try:
        collection = _get_collection(SAVED_COLLECTION)
    except Exception:
        logger.exception("saved_items collection unavailable")
        return False
    doc_id = _saved_doc_id(user_id, name, link)
    try:
        existing = collection.get(ids=[doc_id])
        if not existing.get("ids"):
            return False
        collection.delete(ids=[doc_id])
        return True
    except Exception:
        logger.exception("Failed to unsave item for user %s", user_id)
        return False
