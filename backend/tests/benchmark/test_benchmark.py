"""
Benchmark suite (spec FR13 Layer 3). NOT a regression gate — this measures
directional quality against a golden query set and reports metrics. Run
manually before releases, not on every commit. See spec Testing Strategy.
"""

import json
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.chains.normalizer import normalize_query
from app.graph.retry_loop import run_pipeline
from tests.benchmark.golden_queries import GOLDEN_QUERIES

RESULTS_DIR = Path(__file__).parent.parent.parent / "benchmarks"
REGRESSION_WARNING_THRESHOLD = 0.10  # warn if first-pass rate drops >10%


@dataclass
class QueryOutcome:
    query: str
    normalization_confidence: float
    passed_first_try: bool
    passed_after_retry: bool
    iterations: int
    is_best_available: bool
    latency_seconds: float
    error: str | None = None


def _run_single_query(query: str) -> QueryOutcome:
    start = time.monotonic()
    try:
        normalized = normalize_query(query)

        if normalized.confidence_score < 0.6:
            # Benchmark treats a clarification trigger as a distinct, valid
            # outcome, not a failure — E3 in the golden set exists to prove
            # this path activates correctly, not to be "passed."
            return QueryOutcome(
                query=query,
                normalization_confidence=normalized.confidence_score,
                passed_first_try=False,
                passed_after_retry=False,
                iterations=0,
                is_best_available=False,
                latency_seconds=time.monotonic() - start,
                error="needs_clarification (expected for ambiguous queries)",
            )

        result = run_pipeline(normalized)
        elapsed = time.monotonic() - start

        return QueryOutcome(
            query=query,
            normalization_confidence=normalized.confidence_score,
            passed_first_try=(result.iterations == 1 and not result.is_best_available),
            passed_after_retry=(not result.is_best_available),
            iterations=result.iterations,
            is_best_available=result.is_best_available,
            latency_seconds=elapsed,
        )
    except Exception as exc:
        return QueryOutcome(
            query=query,
            normalization_confidence=0.0,
            passed_first_try=False,
            passed_after_retry=False,
            iterations=0,
            is_best_available=False,
            latency_seconds=time.monotonic() - start,
            error=str(exc),
        )


def _compute_summary(outcomes: list[QueryOutcome]) -> dict:
    latencies = [o.latency_seconds for o in outcomes if o.error is None]
    iterations = [o.iterations for o in outcomes if o.iterations > 0]

    return {
        "total_queries": len(outcomes),
        "first_pass_rate": sum(o.passed_first_try for o in outcomes) / len(outcomes),
        "after_retry_pass_rate": sum(o.passed_after_retry for o in outcomes)
        / len(outcomes),
        "avg_iterations": statistics.mean(iterations) if iterations else 0,
        "p50_latency_seconds": statistics.median(latencies) if latencies else 0,
        "p95_latency_seconds": (
            sorted(latencies)[int(len(latencies) * 0.95)]
            if len(latencies) >= 2
            else (latencies[0] if latencies else 0)
        ),
        "errors": sum(
            1 for o in outcomes if o.error and "needs_clarification" not in o.error
        ),
    }


def _print_table(outcomes: list[QueryOutcome], summary: dict) -> None:
    print("\n" + "=" * 100)
    print(
        f"{'Query':<55} {'1st Pass':<9} {'Retry Pass':<11} {'Iters':<6} {'Latency':<8}"
    )
    print("-" * 100)
    for o in outcomes:
        query_display = (
            (o.query[:52] + "...") if len(o.query) > 52 else (o.query or "(empty)")
        )
        print(
            f"{query_display:<55} {str(o.passed_first_try):<9} {str(o.passed_after_retry):<11} "
            f"{o.iterations:<6} {o.latency_seconds:<8.1f}"
        )
    print("-" * 100)
    print(f"First-pass rate:      {summary['first_pass_rate']:.1%}")
    print(f"After-retry pass rate: {summary['after_retry_pass_rate']:.1%}")
    print(f"Avg iterations:        {summary['avg_iterations']:.2f}")
    print(f"p50 latency:           {summary['p50_latency_seconds']:.1f}s")
    print(f"p95 latency:           {summary['p95_latency_seconds']:.1f}s")
    print(f"Errors (excl. clarification): {summary['errors']}")
    print("=" * 100 + "\n")


def _check_for_regression(summary: dict) -> None:
    """Soft check against the most recent previous run. Warns, never fails
    the test (spec fix: benchmark assertions are soft, not hard gates)."""
    RESULTS_DIR.mkdir(exist_ok=True)
    previous_runs = sorted(RESULTS_DIR.glob("results_*.json"))
    if not previous_runs:
        return

    with open(previous_runs[-1]) as f:
        previous = json.load(f)

    previous_rate = previous["summary"]["first_pass_rate"]
    current_rate = summary["first_pass_rate"]
    if previous_rate - current_rate > REGRESSION_WARNING_THRESHOLD:
        print(
            f"\n⚠️  WARNING: first-pass rate dropped from {previous_rate:.1%} to "
            f"{current_rate:.1%} (more than {REGRESSION_WARNING_THRESHOLD:.0%} drop). "
            f"This could mean a real regression, or it could just mean Tavily's "
            f"live results changed. Investigate before assuming either.\n"
        )


@pytest.mark.integration
@pytest.mark.benchmark
def test_run_benchmark_suite():
    outcomes = [_run_single_query(q) for q in GOLDEN_QUERIES]
    summary = _compute_summary(outcomes)

    _print_table(outcomes, summary)
    _check_for_regression(summary)

    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = RESULTS_DIR / f"results_{timestamp}.json"
    with open(report_path, "w") as f:
        json.dump(
            {
                "timestamp": timestamp,
                "summary": summary,
                "outcomes": [asdict(o) for o in outcomes],
            },
            f,
            indent=2,
        )
    print(f"Report written to {report_path}")
