import asyncio
import logging
from dataclasses import asdict, is_dataclass
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from app import auth_users, pipeline_runner, user_data
from app.auth import verify_api_key
from app.config import get_settings
from app.errors import AppError, ErrorCode
from app.retrieval import memory
from app.routers.users import router as users_router
from app.schemas import SaveItemRequest, SearchRequest, SSEEvent, UnsaveItemRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _current_user_id(request: Request) -> str | None:
    """Resolve the signed-in user's id from the Authorization: Bearer token,
    or None if unauthenticated / invalid. Never raises."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.removeprefix("Bearer ").strip()
    try:
        user = auth_users.get_user_by_token(token)
    except Exception:
        return None
    return user.get("user_id") if user else None

# Sentinel marking the end of a sync generator when pulled one item at a time.
_STREAM_END = object()


def _next_or_sentinel(iterator: Any) -> Any:
    """Return next(iterator), or _STREAM_END when exhausted. Lets us drive a
    sync generator from async code via asyncio.to_thread without letting
    StopIteration cross the thread boundary."""
    try:
        return next(iterator)
    except StopIteration:
        return _STREAM_END

app = FastAPI(title="Agentic RAG Matching Engine")

# Auth routes — no API key required
app.include_router(users_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type", "Authorization"],
    allow_credentials=False,
)


@app.exception_handler(AppError)
async def app_error_handler(
    request: Request,
    exc: AppError,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_response().model_dump(),
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/api/v1/saved",
    dependencies=[Depends(verify_api_key)],
)
async def get_saved_items(http_request: Request) -> dict[str, Any]:
    """Return the signed-in user's saved products. Empty list if not signed in."""
    user_id = _current_user_id(http_request)
    if not user_id:
        return {"products": [], "count": 0}
    products = await asyncio.to_thread(user_data.get_saved, user_id)
    return {"products": products, "count": len(products)}


@app.post(
    "/api/v1/saved",
    dependencies=[Depends(verify_api_key)],
)
async def save_item(body: SaveItemRequest, http_request: Request) -> dict[str, Any]:
    """Save a product for the signed-in user."""
    user_id = _current_user_id(http_request)
    if not user_id:
        raise AppError(
            code=ErrorCode.INVALID_API_KEY,
            message="Sign in to save products.",
        )
    record = await asyncio.to_thread(
        user_data.save_item,
        user_id,
        body.name,
        body.price,
        body.image,
        body.merchant,
        body.link,
    )
    return {"saved": True, "item": record}


@app.delete(
    "/api/v1/saved",
    dependencies=[Depends(verify_api_key)],
)
async def unsave_item(body: UnsaveItemRequest, http_request: Request) -> dict[str, Any]:
    """Remove a product from the signed-in user's saved list."""
    user_id = _current_user_id(http_request)
    if not user_id:
        raise AppError(
            code=ErrorCode.INVALID_API_KEY,
            message="Sign in to manage saved products.",
        )
    removed = await asyncio.to_thread(
        user_data.unsave_item, user_id, body.name, body.link
    )
    return {"removed": removed}


@app.get(
    "/api/v1/history",
    dependencies=[Depends(verify_api_key)],
)
async def get_search_history(http_request: Request) -> dict[str, Any]:
    """Return the signed-in user's search history (newest first)."""
    user_id = _current_user_id(http_request)
    if not user_id:
        return {"searches": [], "count": 0}
    searches = await asyncio.to_thread(user_data.get_history, user_id)
    return {"searches": searches, "count": len(searches)}


def _serialize(value: Any) -> Any:
    """Convert project models/dataclasses into JSON-compatible values."""

    if value is None:
        return None

    if hasattr(value, "model_dump"):
        return value.model_dump()

    if is_dataclass(value):
        return asdict(value)

    if isinstance(value, list):
        return [_serialize(item) for item in value]

    if isinstance(value, tuple):
        return [_serialize(item) for item in value]

    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}

    return value


def _result_payload(
    result: pipeline_runner.PipelineResult,
) -> dict[str, Any]:
    products = []
    for matched in result.matched:
        product = matched.product
        products.append(
            {
                "name": product.get_name(),
                "price": product.get_price(),
                "matched_constraints": matched.matched_constraints,
                "soft_score": matched.soft_score,
                "fields": _serialize(product.fields),
            }
        )

    verdict = result.verdict
    feedback = getattr(verdict, "feedback", None)
    return {
        "products": products,
        "synthesis": result.synthesis,
        "metadata": {
            "iterations": result.iterations,
            "is_best_available": result.is_best_available,
            "from_cache": getattr(result, "from_cache", False),
            "weighted_score": verdict.weighted_score,
            "assumptions_made": [],
            "from_memory": False,
            "memory_similarity": None,
            "generated_queries": getattr(result, "generated_queries", []),
            "logs": getattr(result, "logs", []),
            "verdict": {
                "verdict": "PASS" if verdict.passed else "RETRY",
                "weighted_score": verdict.weighted_score,
                "relevance_score": verdict.relevance,
                "constraint_score": verdict.requirement_match,
                "evidence_score": verdict.evidence_quality,
                "completeness_score": verdict.completeness,
                "rationale": _build_rationale(result),
                # The critic's real feedback (its "thinking"), not a canned line.
                "feedback": _serialize(feedback) if feedback else None,
            },
        },
    }


def _shortest_ttl(result: pipeline_runner.PipelineResult) -> str:
    """The earliest per-field ttl_expires_at across every matched product, so
    memory freshness is bounded by the most volatile field (price = 6h). Empty
    string when nothing has a TTL (treated as always-stale by memory lookup)."""
    ttls: list[str] = []
    for matched in result.matched:
        for field in matched.product.fields.values():
            if field.ttl_expires_at:
                ttls.append(field.ttl_expires_at)
    return min(ttls) if ttls else ""


def _build_rationale(result: pipeline_runner.PipelineResult) -> str:
    """A human-readable rationale derived from real critic scores/feedback,
    never a hardcoded claim."""
    v = result.verdict
    if v.passed:
        return (
            f"Verified: relevance {v.relevance}/10, requirement match "
            f"{v.requirement_match}/10, evidence quality {v.evidence_quality}/10, "
            f"completeness {v.completeness}/10 (weighted {v.weighted_score}/10)."
        )
    parts: list[str] = []
    fb = getattr(v, "feedback", None)
    if fb:
        if fb.failed_criteria:
            parts.append("Unmet: " + "; ".join(fb.failed_criteria))
        if fb.missing_data:
            parts.append("Missing: " + "; ".join(fb.missing_data))
    base = (
        f"Closest available (weighted {v.weighted_score}/10); the critic could not "
        f"fully verify every requirement."
    )
    return base + (" " + " ".join(parts) if parts else "")


def _get_distinct_clarification_question(
    normalized_query: Any,
    current_round: int,
    previous_questions: list[str],
) -> str:
    category = getattr(normalized_query, "category", "item")
    if not category or category == "products":
        category = "product"

    if current_round <= 1 or not previous_questions:
        candidate = f"What is your target budget or primary use case for this {category}?"
    else:
        candidate = f"Do you have any specific feature preferences (like battery life, connectivity, or design) or brand choices for {category}?"

    if candidate in previous_questions:
        candidate = f"Any additional feature or price requirement for your {category} search?"

    return candidate


@app.post(
    "/api/v1/search",
    dependencies=[Depends(verify_api_key)],
)
async def search(request: SearchRequest, http_request: Request) -> StreamingResponse:
    clarification_context = request.clarification_context
    user_id = _current_user_id(http_request)

    if clarification_context is None:
        clarification_context_value = "none"
    elif hasattr(clarification_context, "model_dump"):
        clarification_context_value = str(clarification_context.model_dump())
    else:
        clarification_context_value = str(clarification_context)

    async def event_stream():
        try:
            normalized_query = await asyncio.to_thread(
                pipeline_runner.normalize_query,
                request.query,
                clarification_context=clarification_context_value,
            )
        except AppError as exc:
            yield SSEEvent(
                event="error",
                payload=exc.to_response().error.model_dump(),
            ).to_sse_line()
            return
        except Exception:
            logging.exception("Query normalization failed")
            yield SSEEvent(
                event="error",
                payload={
                    "code": ErrorCode.PROVIDER_UNAVAILABLE,
                    "message": "Unable to understand the request right now. Please try again.",
                    "details": None,
                },
            ).to_sse_line()
            return

        # -----------------------------------------
        # LOW CONFIDENCE (Max 1-2 clarification rounds)
        # -----------------------------------------

        current_round = 1
        previous_questions: list[str] = []
        user_answers: list[str] = []

        if clarification_context is not None:
            if isinstance(clarification_context, dict):
                current_round = int(clarification_context.get("round", 1))
                previous_questions = list(clarification_context.get("previous_questions", []))
                user_answers = list(clarification_context.get("user_answers", []))
            elif hasattr(clarification_context, "round"):
                current_round = int(getattr(clarification_context, "round", 1))
                previous_questions = list(getattr(clarification_context, "previous_questions", []))
                user_answers = list(getattr(clarification_context, "user_answers", []))

        # Spec FR2: hard cap of 2 clarification rounds. After 2 rounds have been
        # asked (or 2 user answers collected), proceed with best-effort assumptions.
        max_clarifications_reached = (current_round > 2) or (len(user_answers) >= 2) or (len(previous_questions) >= 2)

        # Spec FR1/FR2: confidence below 0.6 triggers the clarification path.
        if normalized_query.confidence_score < 0.6 and not max_clarifications_reached:
            question = _get_distinct_clarification_question(
                normalized_query,
                current_round,
                previous_questions,
            )
            event = SSEEvent(
                event="needs_clarification",
                payload={
                    "query": _serialize(normalized_query),
                    "question": question,
                    "round": current_round,
                },
            )

            yield event.to_sse_line()
            return

        # -----------------------------------------
        # PROGRESS
        # -----------------------------------------

        # Normalization already completed above.
        yield SSEEvent(
            event="progress",
            payload={"stage": "normalizing", "message": "Understood your requirements."},
        ).to_sse_line()

        # -----------------------------------------
        # SEMANTIC MEMORY LOOKUP (query-level RAG recall)
        # -----------------------------------------
        # Before running the pipeline, check whether this exact/near-exact query
        # was answered before and is still fresh. On a hit we serve the stored
        # response straight from ChromaDB: no Tavily, no pipeline.
        memory_hit = await asyncio.to_thread(memory.lookup_response, request.query)
        if memory_hit is not None:
            stored_payload, similarity = memory_hit
            pct = round(similarity * 100)
            yield SSEEvent(
                event="progress",
                payload={
                    "stage": "cache_hit",
                    "message": (
                        f"Answered from memory — matched an earlier query at "
                        f"{pct}% similarity. Skipping live web search."
                    ),
                },
            ).to_sse_line()

            metadata = stored_payload.setdefault("metadata", {})
            metadata["from_memory"] = True
            metadata["memory_similarity"] = round(similarity, 4)
            logs = metadata.setdefault("logs", [])
            logs.append(
                {
                    "stage": "cache_hit",
                    "title": "Semantic Memory Recall (ChromaDB)",
                    "detail": (
                        f"Served the full verified response from long-term vector "
                        f"memory at {pct}% query similarity. Tavily and the pipeline "
                        f"were skipped entirely."
                    ),
                    "type": "memory",
                }
            )

            if user_id:
                products = stored_payload.get("products") or []
                best = products[0] if products else None
                best_name = best.get("name") if best else None
                best_price = best.get("price") if best else None
                best_url = None
                if best:
                    name_field = (best.get("fields") or {}).get("name")
                    if isinstance(name_field, dict):
                        best_url = name_field.get("source_url")
                await asyncio.to_thread(
                    user_data.record_search,
                    user_id,
                    request.query,
                    best_name,
                    best_price,
                    best_url,
                )

            yield SSEEvent(event="result", payload=stored_payload).to_sse_line()
            return

        # -----------------------------------------
        # RUN PIPELINE (real-time stage streaming)
        # -----------------------------------------
        # run_pipeline_streaming runs the pipeline on a worker thread and yields
        # a stage event exactly when each stage starts, then the PipelineResult.
        # We pull items off that sync generator one at a time in a thread so the
        # SSE stream reflects real progress instead of a fixed up-front burst.

        result: pipeline_runner.PipelineResult | None = None
        try:
            stream = pipeline_runner.run_pipeline_streaming(normalized_query)
            while True:
                item = await asyncio.to_thread(_next_or_sentinel, stream)
                if item is _STREAM_END:
                    break
                if isinstance(item, pipeline_runner.PipelineResult):
                    result = item
                    break
                # Otherwise it's a {"stage", "message"} progress event.
                yield SSEEvent(event="progress", payload=item).to_sse_line()
        except AppError as exc:
            yield SSEEvent(
                event="error",
                payload=exc.to_response().error.model_dump(),
            ).to_sse_line()
            return
        except Exception:
            logging.exception("Search pipeline failed")
            yield SSEEvent(
                event="error",
                payload={
                    "code": ErrorCode.INTERNAL_ERROR,
                    "message": "Search pipeline failed. Please try again.",
                    "details": None,
                },
            ).to_sse_line()
            return

        if result is None:
            yield SSEEvent(
                event="error",
                payload={
                    "code": ErrorCode.INTERNAL_ERROR,
                    "message": "Search pipeline produced no result. Please try again.",
                    "details": None,
                },
            ).to_sse_line()
            return

        # -----------------------------------------
        # RECORD SEARCH HISTORY (best-effort, per user)
        # -----------------------------------------
        if user_id:
            best = result.matched[0] if result.matched else None
            best_name = best.product.get_name() if best else None
            best_price = best.product.get_price() if best else None
            best_url = None
            if best:
                name_field = best.product.fields.get("name")
                best_url = name_field.source_url if name_field else None
            await asyncio.to_thread(
                user_data.record_search,
                user_id,
                request.query,
                best_name,
                best_price,
                best_url,
            )

        # -----------------------------------------
        # FINAL RESULT
        # -----------------------------------------

        payload = _result_payload(result)

        # -----------------------------------------
        # RECORD RESPONSE TO SEMANTIC MEMORY (best-effort)
        # -----------------------------------------
        # Only store answers that actually returned products, and bound their
        # freshness by the shortest per-field TTL of those products.
        if result.matched:
            await asyncio.to_thread(
                memory.record_response,
                request.query,
                payload,
                _shortest_ttl(result),
            )

        yield SSEEvent(event="result", payload=payload).to_sse_line()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
