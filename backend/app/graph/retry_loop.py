from __future__ import annotations

import queue
import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.chains.critic import critique_results
from app.chains.extractor import extract_products
from app.chains.generator import generate_search_queries
from app.chains.matcher import MatchedProduct, match_products
from app.chains.synthesizer import synthesize_answer
from app.models.critic import CriticFeedback, CriticVerdict
from app.models.query import NormalizedQuery
from app.retrieval.cache import check_cache_sufficiency, persist_products
from app.retrieval.tavily_client import search_products

MAX_ITERATIONS = 3
PLATEAU_THRESHOLD = 0.5

# A progress emitter takes (stage, message) and reports it in real time.
EmitFn = Callable[[str, str], None]


def _noop_emit(stage: str, message: str) -> None:
    """Default emitter: does nothing (used by the non-streaming run_pipeline)."""


class _PipelineState(TypedDict):
    query: NormalizedQuery
    feedback: CriticFeedback
    matched: list[MatchedProduct]
    verdict: CriticVerdict | None
    iteration: int
    score_history: list[float]
    best_matched: list[MatchedProduct]
    best_verdict: CriticVerdict | None
    synthesis: str | None
    from_cache: bool
    generated_queries: list[str]
    logs: list[dict[str, Any]]
    done: bool
    # Real-time progress emitter. Not serialized; only used during execution.
    emit: EmitFn


@dataclass
class PipelineResult:
    matched: list[MatchedProduct]
    synthesis: str | None
    verdict: CriticVerdict
    iterations: int
    is_best_available: bool
    from_cache: bool = False
    generated_queries: list[str] = field(default_factory=list)
    logs: list[dict[str, Any]] = field(default_factory=list)


def _emit(state: _PipelineState, stage: str, message: str) -> None:
    fn = state.get("emit") or _noop_emit
    try:
        fn(stage, message)
    except Exception:
        # A failed progress emit must never break the pipeline.
        pass


def _retrieve_and_match_node(state: _PipelineState) -> _PipelineState:
    """One iteration: check cache first, fall back to live search if insufficient.

    Emits a progress event immediately before each real sub-step so the client
    sees stages update as they actually happen, not on a timer.
    """
    query = state["query"]
    logs = state.setdefault("logs", [])
    query_text = f"{query.category} {' '.join(query.constraints)} {' '.join(query.preferences)}"

    is_retry = state["iteration"] >= 1
    if is_retry:
        _emit(state, "retrying", "Refining the search with critic feedback...")

    _emit(state, "searching", "Checking cached results...")
    cached_products = check_cache_sufficiency(query_text, category=query.category)

    if cached_products:
        products = cached_products
        state["from_cache"] = True
        _emit(
            state,
            "cache_hit",
            f"Found {len(cached_products)} verified products in cache.",
        )
        logs.append({
            "stage": "cache_check",
            "title": "ChromaDB Vector Cache Hit",
            "detail": f"Retrieved {len(cached_products)} verified product embeddings directly from long-term memory for category '{query.category}' in 0ms.",
            "type": "memory",
        })
    else:
        _emit(state, "generating", "Formulating targeted search queries...")
        queries = generate_search_queries(query, feedback=state["feedback"])
        state["generated_queries"] = queries
        logs.append({
            "stage": "generating",
            "title": "Query Generator (LCEL)",
            "detail": f"Formulated {len(queries)} targeted web retrieval queries: {', '.join(queries[:3])}",
            "type": "search",
        })

        _emit(state, "searching", f"Searching the web with {len(queries)} queries...")
        search_results = search_products(queries)
        logs.append({
            "stage": "searching",
            "title": "Tavily Real-Time Web Scraping",
            "detail": f"Fetched {len(search_results)} live web pages across merchant indexes (Croma, Amazon, Flipkart, etc.).",
            "type": "retrieval",
        })

        _emit(state, "extracting", f"Extracting products from {len(search_results)} pages...")
        products = extract_products(search_results)
        logs.append({
            "stage": "extracting",
            "title": "Structured Product Extractor",
            "detail": f"Parsed {len(products)} structured product entities with verified prices, attributes, and specifications.",
            "type": "extraction",
        })
        persist_products(products, category=query.category)
        state["from_cache"] = False

    _emit(state, "matching", "Matching products against your constraints...")
    matched = match_products(products, query)
    state["matched"] = matched
    logs.append({
        "stage": "matching",
        "title": "Constraint & Preference Matching",
        "detail": f"Filtered {len(matched)} valid products satisfying hard budget (₹{query.budget.min} - ₹{query.budget.max}) and scored feature match relevance.",
        "type": "filter",
    })
    state["iteration"] += 1
    return state


def _critique_node(state: _PipelineState) -> _PipelineState:
    _emit(state, "critiquing", "Scoring and verifying candidate matches...")
    verdict = critique_results(state["matched"], state["query"])
    state["verdict"] = verdict
    state["score_history"].append(verdict.weighted_score)
    logs = state.setdefault("logs", [])

    status_str = "PASS" if verdict.passed else "RETRY"
    logs.append({
        "stage": "critiquing",
        "title": "LLM Critic Rubric Judge",
        "detail": f"Verdict: {status_str} (Score: {verdict.weighted_score:.1f}/10). Relevance: {verdict.relevance}/10, Match: {verdict.requirement_match}/10, Evidence: {verdict.evidence_quality}/10, Completeness: {verdict.completeness}/10.",
        "type": "critic",
    })

    # Track best-scoring attempt across all iterations for the fallback path.
    if state["best_verdict"] is None or verdict.weighted_score > state["best_verdict"].weighted_score:
        state["best_verdict"] = verdict
        state["best_matched"] = state["matched"]

    return state


def _route_after_critique(state: _PipelineState) -> str:
    verdict = state["verdict"]
    assert verdict is not None

    if verdict.passed:
        return "synthesize"

    iteration = state["iteration"]
    if iteration >= MAX_ITERATIONS:
        return "best_available"

    history = state["score_history"]
    if len(history) >= 2:
        delta = history[-1] - history[-2]
        if delta < PLATEAU_THRESHOLD:
            return "best_available"

    state["feedback"] = verdict.feedback
    return "retry"


def _synthesize_node(state: _PipelineState) -> _PipelineState:
    _emit(state, "synthesizing", "Writing your personalized recommendation...")
    synthesis = synthesize_answer(state["matched"], state["query"])
    state["synthesis"] = synthesis
    logs = state.setdefault("logs", [])
    logs.append({
        "stage": "synthesizing",
        "title": "Recommendation Synthesizer",
        "detail": "Synthesized source-grounded plain-English recommendation linking direct merchant citations.",
        "type": "synthesis",
    })
    return state


def _best_available_node(state: _PipelineState) -> _PipelineState:
    _emit(state, "synthesizing", "Preparing the best available matches...")
    state["matched"] = state["best_matched"]
    state["verdict"] = state["best_verdict"]
    state["synthesis"] = None
    return state


def _build_graph() -> StateGraph:
    graph = StateGraph(_PipelineState)
    graph.add_node("retrieve_and_match", _retrieve_and_match_node)
    graph.add_node("critique", _critique_node)
    graph.add_node("synthesize", _synthesize_node)
    graph.add_node("best_available", _best_available_node)

    graph.set_entry_point("retrieve_and_match")
    graph.add_edge("retrieve_and_match", "critique")
    graph.add_conditional_edges(
        "critique",
        _route_after_critique,
        {
            "synthesize": "synthesize",
            "best_available": "best_available",
            "retry": "retrieve_and_match",
        },
    )
    graph.add_edge("synthesize", END)
    graph.add_edge("best_available", END)
    return graph


def _initial_state(query: NormalizedQuery, emit: EmitFn) -> _PipelineState:
    return {
        "query": query,
        "feedback": CriticFeedback(),
        "matched": [],
        "verdict": None,
        "iteration": 0,
        "score_history": [],
        "best_matched": [],
        "best_verdict": None,
        "synthesis": None,
        "from_cache": False,
        "generated_queries": [],
        "logs": [{
            "stage": "normalizing",
            "title": "Query Normalizer Intent Extraction",
            "detail": f"Parsed category '{query.category}', use case '{query.use_case}', budget range ₹{query.budget.min} - ₹{query.budget.max}, constraints {query.constraints}, and preferences {query.preferences}.",
            "type": "normalizer",
        }],
        "done": False,
        "emit": emit,
    }


def _result_from_state(final_state: _PipelineState) -> PipelineResult:
    verdict = final_state["verdict"]
    assert verdict is not None
    return PipelineResult(
        matched=final_state["matched"],
        synthesis=final_state["synthesis"],
        verdict=verdict,
        iterations=final_state["iteration"],
        is_best_available=(final_state["synthesis"] is None),
        from_cache=final_state.get("from_cache", False),
        generated_queries=final_state.get("generated_queries", []),
        logs=final_state.get("logs", []),
    )


def run_pipeline(
    query: NormalizedQuery, emit: EmitFn | None = None
) -> PipelineResult:
    """Run the full pipeline synchronously. `emit` receives (stage, message)
    events in real time as each stage runs; defaults to a no-op."""
    graph = _build_graph().compile()
    final_state = graph.invoke(_initial_state(query, emit or _noop_emit))
    return _result_from_state(final_state)


# Sentinel pushed onto the queue when the pipeline is finished.
class _StageEvent(TypedDict):
    stage: str
    message: str


def run_pipeline_streaming(
    query: NormalizedQuery,
) -> Iterator[_StageEvent | PipelineResult]:
    """Run the pipeline on a worker thread and yield stage events as they
    actually occur, followed by the final PipelineResult.

    Each item is either a dict {"stage", "message"} (progress) or the terminal
    PipelineResult. Any exception raised inside the pipeline is re-raised here.
    """
    events: queue.Queue[Any] = queue.Queue()
    _DONE = object()
    result_box: dict[str, Any] = {}

    def emit(stage: str, message: str) -> None:
        events.put({"stage": stage, "message": message})

    def worker() -> None:
        try:
            result_box["result"] = run_pipeline(query, emit=emit)
        except Exception as exc:  # surface to the consumer
            result_box["error"] = exc
        finally:
            events.put(_DONE)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    while True:
        item = events.get()
        if item is _DONE:
            break
        yield item

    thread.join()

    if "error" in result_box:
        raise result_box["error"]
    yield result_box["result"]
