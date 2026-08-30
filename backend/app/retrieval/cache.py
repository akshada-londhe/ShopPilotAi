import logging
from datetime import datetime, timezone
from functools import lru_cache

import chromadb
from chromadb import Collection
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from app.config import get_settings
from app.models.product import ProductEntity

logger = logging.getLogger(__name__)

# Spec FR4: a cached result is "relevant" if cosine_similarity >= 0.85.
SIMILARITY_THRESHOLD = 0.85
MIN_SUFFICIENT_RESULTS = 3
COLLECTION_NAME = 'products'

@lru_cache
def _get_embedder() -> DefaultEmbeddingFunction:
    return DefaultEmbeddingFunction()

@lru_cache
def _get_client() -> chromadb.ClientAPI:
    settings = get_settings()
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)

def get_chroma_collection() -> Collection:
    client = _get_client()
    return client.get_or_create_collection(
        COLLECTION_NAME,
        metadata={'hnsw:space': 'cosine'},
    )

import os
import shutil

def _embed_text(text: str) -> list[float]:
    try:
        return [float(value) for value in _get_embedder()([text])[0]]
    except Exception as e:
        logger.warning(f"Embedding calculation failed ({e}), attempting ONNX cache cleanup and retry")
        for path in [
            os.path.expanduser("~/.cache/chroma/onnx_models"),
            "/opt/render/.cache/chroma/onnx_models",
        ]:
            if os.path.exists(path):
                try:
                    shutil.rmtree(path, ignore_errors=True)
                except Exception:
                    pass
        try:
            _get_embedder.cache_clear()
            return [float(value) for value in _get_embedder()([text])[0]]
        except Exception:
            logger.error("ONNX embedding retry failed, returning fallback zero vector")
            return [0.0] * 384

def _product_to_document_text(product: ProductEntity) -> str:
    parts = []
    for name, field in product.fields.items():
        parts.append(f'{name}: {field.value}')
    return ' | '.join(parts)

def persist_products(products: list[ProductEntity], category: str, saved: bool = False) -> None:
    if not products:
        return
    try:
        collection = get_chroma_collection()
    except Exception:
        logger.exception('ChromaDB collection unavailable, treating cache as empty')
        return
    ids = [product.entity_id for product in products]
    documents = [_product_to_document_text(product) for product in products]
    embeddings = [_embed_text(document) for document in documents]
    metadatas = [
        {
            'extracted_at': product.extracted_at,
            'ttl_expires_at': product.ttl_expires_at,
            'category': category,
            'source_url': next(iter(product.fields.values())).source_url if product.fields else '',
            'product_json': product.model_dump_json(),
            'saved': saved,
        }
        for product in products
    ]
    try:
        collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    except Exception:
        logger.exception('Failed to persist %d products to ChromaDB', len(products))

def _ttl_is_future(ttl_str: str | None) -> bool:
    if not ttl_str:
        return False
    ttl = datetime.fromisoformat(ttl_str)
    if ttl.tzinfo is None:
        ttl = ttl.replace(tzinfo=timezone.utc)
    return ttl > datetime.now(timezone.utc)


def _is_fresh(product: ProductEntity) -> bool:
    """Spec FR4: a cached result is fresh only if ttl_expires_at is in the
    future for ALL of its fields."""
    if not product.fields:
        return _ttl_is_future(product.ttl_expires_at)
    return all(
        _ttl_is_future(field.ttl_expires_at) for field in product.fields.values()
    )

def check_cache_sufficiency(query_text: str, category: str) -> list[ProductEntity]:
    try:
        collection = get_chroma_collection()
    except Exception:
        logger.exception('ChromaDB collection unavailable, treating cache as empty')
        return []
    query_embedding = _embed_text(query_text)
    try:
        raw_results = collection.query(query_embeddings=[query_embedding], n_results=10, where={'category': category})
    except Exception:
        logger.exception('ChromaDB query failed, treating cache as empty')
        return []
    if not raw_results['ids'] or not raw_results['ids'][0]:
        return []
    distances = raw_results['distances'][0]
    metadatas = raw_results['metadatas'][0]
    sufficient: list[ProductEntity] = []
    for distance, metadata in zip(distances, metadatas):
        similarity = 1 - distance
        logger.debug('CACHE DEBUG | distance=%.4f similarity=%.4f category=%s', distance, similarity, metadata.get('category'))
        if similarity < SIMILARITY_THRESHOLD:
            continue
        product = ProductEntity.model_validate_json(metadata['product_json'])
        if _is_fresh(product):
            sufficient.append(product)
    if len(sufficient) < MIN_SUFFICIENT_RESULTS:
        return []
    return sufficient
