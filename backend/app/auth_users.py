"""ChromaDB-backed user store.

Users are stored in a separate 'users' collection in the same ChromaDB
instance that already holds products. Each document is the user's email
(used as the collection ID), and the metadata holds the bcrypt-hashed
password, display name, and timestamps.

JWT tokens are signed with the SECRET_KEY env variable (falls back to
backend_api_key if not set, which is fine for local dev).
"""

from __future__ import annotations

import hashlib
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

import chromadb
from chromadb import Collection

logger = logging.getLogger(__name__)

import bcrypt


def _hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    try:
        pwd_bytes = password.encode("utf-8")[:72]
        return bcrypt.checkpw(pwd_bytes, hashed.encode("utf-8"))
    except Exception:
        return False


def _jwt():
    from jose import jwt as _jose_jwt  # type: ignore[import-untyped]
    return _jose_jwt


# ── Constants ────────────────────────────────────────────────────────────────
USERS_COLLECTION = "users"
TOKEN_EXPIRE_HOURS = 72
ALGORITHM = "HS256"


def _secret_key() -> str:
    from app.config import get_settings  # local import avoids circular dep

    settings = get_settings()
    # Prefer the dedicated JWT secret (env JWT_SECRET is read by pydantic-settings
    # into jwt_secret). Fall back to the API key for local dev, but warn: reusing
    # the API key to sign tokens is unsafe in production.
    secret = os.environ.get("JWT_SECRET") or settings.jwt_secret
    if not secret:
        logger.warning(
            "JWT_SECRET is not set; signing tokens with backend_api_key. "
            "Set JWT_SECRET to a long random value in production."
        )
        secret = settings.backend_api_key
    return secret


# ── ChromaDB client (shared with cache.py via same path) ────────────────────
@lru_cache
def _get_client() -> chromadb.ClientAPI:
    from app.config import get_settings
    return chromadb.PersistentClient(path=get_settings().chroma_persist_dir)


def _get_users_collection() -> Collection:
    client = _get_client()
    return client.get_or_create_collection(
        USERS_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


# ── Helpers ──────────────────────────────────────────────────────────────────
def _email_id(email: str) -> str:
    """Stable document ID derived from the normalised email."""
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()


def _make_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return _jwt().encode(payload, _secret_key(), algorithm=ALGORITHM)


def _verify_token(token: str) -> dict[str, Any] | None:
    try:
        return _jwt().decode(token, _secret_key(), algorithms=[ALGORITHM])
    except Exception:
        return None


# ── Helpers ──────────────────────────────────────────────────────────────────
def _prepare_password(password: str) -> str:
    """Safely truncate password to 72 bytes max for bcrypt."""
    if not password:
        return ""
    truncated = password[:72]
    encoded = truncated.encode("utf-8")[:72]
    return encoded.decode("utf-8", errors="ignore")


# ── Public API ───────────────────────────────────────────────────────────────
def create_user(name: str, email: str, password: str) -> dict[str, Any]:
    """Register a new user.  Raises ValueError if the email already exists."""
    email = email.strip().lower()
    doc_id = _email_id(email)
    col = _get_users_collection()

    # Check duplicate
    existing = col.get(ids=[doc_id])
    if existing["ids"]:
        raise ValueError("An account with this email already exists.")

    user_id = str(uuid.uuid4())
    pw_hash = _hash_password(password)
    now = datetime.now(timezone.utc).isoformat()

    col.add(
        ids=[doc_id],
        documents=[email],          # searched by email
        embeddings=[[0.0] * 384],   # dummy embedding — users don't need ANN
        metadatas=[{
            "user_id": user_id,
            "name": name,
            "email": email,
            "pw_hash": pw_hash,
            "created_at": now,
        }],
    )

    token = _make_token(user_id, email)
    return {"user_id": user_id, "name": name, "email": email, "token": token}


def authenticate_user(email: str, password: str) -> dict[str, Any]:
    """Verify credentials.  Raises ValueError on bad email/password."""
    email = email.strip().lower()
    doc_id = _email_id(email)
    col = _get_users_collection()

    result = col.get(ids=[doc_id])
    if not result["ids"]:
        raise ValueError("No account found with that email.")

    meta = result["metadatas"][0]
    if not _verify_password(password, meta["pw_hash"]):
        raise ValueError("Incorrect password.")

    token = _make_token(meta["user_id"], email)
    return {
        "user_id": meta["user_id"],
        "name": meta["name"],
        "email": meta["email"],
        "token": token,
    }


def get_user_by_token(token: str) -> dict[str, Any] | None:
    """Decode JWT and return user info, or None if token is invalid/expired."""
    payload = _verify_token(token)
    if not payload:
        return None

    email = payload.get("email", "")
    doc_id = _email_id(email)
    col = _get_users_collection()
    result = col.get(ids=[doc_id])
    if not result["ids"]:
        return None

    meta = result["metadatas"][0]
    return {
        "user_id": meta["user_id"],
        "name": meta["name"],
        "email": meta["email"],
        "created_at": meta.get("created_at"),
    }


def delete_user(email: str) -> bool:
    """Delete a user by email. Returns True if deleted, False if not found.
    Used for cleanup of broken/test accounts.
    """
    email = email.strip().lower()
    doc_id = _email_id(email)
    col = _get_users_collection()
    existing = col.get(ids=[doc_id])
    if not existing["ids"]:
        return False
    col.delete(ids=[doc_id])
    return True
