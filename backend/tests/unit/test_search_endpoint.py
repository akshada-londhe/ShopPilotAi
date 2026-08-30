from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.critic import CriticFeedback, CriticVerdict
from app.models.query import Budget, NormalizedQuery

client = TestClient(app)

API_KEY_HEADER = {"X-API-Key": "test-key-123"}


def passing_verdict() -> CriticVerdict:
    return CriticVerdict(
        relevance=8,
        requirement_match=8,
        evidence_quality=8,
        completeness=8,
        contradiction_flag=False,
        feedback=CriticFeedback(),
    )


def test_search_endpoint_rejects_missing_api_key():
    response = client.post("/api/v1/search", json={"query": "gaming mouse under 2000"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_api_key"


def test_search_endpoint_streams_progress_and_result():
    with (
        patch("app.auth.get_settings") as mock_settings,
        patch("app.pipeline_runner.normalize_query") as mock_normalize,
        patch("app.pipeline_runner.run_pipeline_streaming") as mock_stream,
        patch("app.main.memory.lookup_response", return_value=None),
        patch("app.main.memory.record_response"),
    ):
        mock_settings.return_value.backend_api_key = "test-key-123"
        mock_normalize.return_value = NormalizedQuery(
            intent="purchase",
            category="mouse",
            budget=Budget(min=0, max=2000, currency="INR"),
            constraints=[],
            preferences=[],
            use_case="gaming",
            confidence_score=0.9,
        )

        from app.graph.retry_loop import PipelineResult

        result = PipelineResult(
            matched=[],
            synthesis="Great pick!",
            verdict=passing_verdict(),
            iterations=1,
            is_best_available=False,
        )

        def _fake_stream(_query):
            # Real-time stage events, then the terminal result.
            yield {"stage": "searching", "message": "Searching..."}
            yield {"stage": "matching", "message": "Matching..."}
            yield result

        mock_stream.side_effect = _fake_stream

        response = client.post(
            "/api/v1/search",
            json={"query": "gaming mouse under 2000"},
            headers=API_KEY_HEADER,
        )

    assert response.status_code == 200
    body = response.text
    assert '"event": "progress"' in body
    assert '"stage": "searching"' in body
    assert '"event": "result"' in body
    assert "Great pick!" in body


def test_search_endpoint_emits_needs_clarification_on_low_confidence():
    with (
        patch("app.auth.get_settings") as mock_settings,
        patch("app.pipeline_runner.normalize_query") as mock_normalize,
    ):
        mock_settings.return_value.backend_api_key = "test-key-123"
        mock_normalize.return_value = NormalizedQuery(
            intent="unknown",
            category="unknown",
            budget=Budget(min=0, max=10000000, currency="INR"),
            constraints=[],
            preferences=[],
            use_case="unknown",
            confidence_score=0.3,
        )

        response = client.post(
            "/api/v1/search",
            json={"query": "phone"},
            headers=API_KEY_HEADER,
        )

    body = response.text
    assert '"event": "needs_clarification"' in body


def test_search_endpoint_emits_error_when_pipeline_fails():
    with (
        patch("app.auth.get_settings") as mock_settings,
        patch("app.pipeline_runner.normalize_query") as mock_normalize,
        patch("app.pipeline_runner.run_pipeline_streaming") as mock_stream,
        patch("app.main.memory.lookup_response", return_value=None),
        patch("app.main.memory.record_response"),
    ):
        def _boom(_query):
            raise RuntimeError("quota")
            yield  # pragma: no cover  (makes this a generator)

        mock_stream.side_effect = _boom
        mock_settings.return_value.backend_api_key = "test-key-123"
        mock_normalize.return_value = NormalizedQuery(
            intent="purchase",
            category="mouse",
            budget=Budget(min=0, max=2000, currency="INR"),
            constraints=[],
            preferences=[],
            use_case="gaming",
            confidence_score=0.9,
        )

        response = client.post(
            "/api/v1/search",
            json={"query": "gaming mouse under 2000"},
            headers=API_KEY_HEADER,
        )

    assert response.status_code == 200
    assert '"event": "error"' in response.text
    assert "Search pipeline failed" in response.text


def _normalized(**overrides) -> NormalizedQuery:
    base: dict = {
        "intent": "purchase",
        "category": "mouse",
        "budget": Budget(min=0, max=2000, currency="INR"),
        "constraints": [],
        "preferences": [],
        "use_case": "gaming",
        "confidence_score": 0.9,
    }
    base.update(overrides)
    return NormalizedQuery(**base)


def test_memory_hit_skips_pipeline_and_flags_from_memory():
    stored_payload = {
        "products": [{"name": "Logitech G502", "price": 1999, "fields": {}}],
        "synthesis": "Recalled answer",
        "metadata": {"iterations": 1, "is_best_available": False},
    }

    with (
        patch("app.auth.get_settings") as mock_settings,
        patch("app.pipeline_runner.normalize_query") as mock_normalize,
        patch("app.pipeline_runner.run_pipeline_streaming") as mock_stream,
        patch("app.main.memory.lookup_response") as mock_lookup,
        patch("app.main.memory.record_response") as mock_record,
    ):
        mock_settings.return_value.backend_api_key = "test-key-123"
        mock_normalize.return_value = _normalized()
        mock_lookup.return_value = (stored_payload, 1.0)

        response = client.post(
            "/api/v1/search",
            json={"query": "gaming mouse under 2000"},
            headers=API_KEY_HEADER,
        )

    assert response.status_code == 200
    body = response.text
    assert '"event": "result"' in body
    assert '"from_memory": true' in body
    assert "Recalled answer" in body
    # The pipeline must not run on a memory hit.
    mock_stream.assert_not_called()
    # A hit re-serving an existing entry does not re-record it.
    mock_record.assert_not_called()


def test_memory_miss_runs_pipeline_then_records():
    from app.chains.matcher import MatchedProduct
    from app.graph.retry_loop import PipelineResult
    from app.models.product import ExtractedField, ProductEntity

    product = ProductEntity(
        entity_id="p1",
        fields={
            "name": ExtractedField(
                value="Logitech G502",
                source_url="https://x.com",
                snippet="",
                ttl_expires_at="2099-01-01T00:00:00+00:00",
            ),
            "price": ExtractedField(
                value=1999,
                source_url="https://x.com",
                snippet="",
                ttl_expires_at="2099-01-01T00:00:00+00:00",
            ),
        },
        extracted_at="2026-01-01T00:00:00+00:00",
        ttl_expires_at="2099-01-01T00:00:00+00:00",
    )
    matched = MatchedProduct(product=product, matched_constraints=[], soft_score=8.0)
    result = PipelineResult(
        matched=[matched],
        synthesis="Live answer",
        verdict=passing_verdict(),
        iterations=1,
        is_best_available=False,
    )

    def _fake_stream(_query):
        yield {"stage": "searching", "message": "Searching..."}
        yield result

    with (
        patch("app.auth.get_settings") as mock_settings,
        patch("app.pipeline_runner.normalize_query") as mock_normalize,
        patch("app.pipeline_runner.run_pipeline_streaming") as mock_stream,
        patch("app.main.memory.lookup_response") as mock_lookup,
        patch("app.main.memory.record_response") as mock_record,
    ):
        mock_settings.return_value.backend_api_key = "test-key-123"
        mock_normalize.return_value = _normalized()
        mock_lookup.return_value = None
        mock_stream.side_effect = _fake_stream

        response = client.post(
            "/api/v1/search",
            json={"query": "gaming mouse under 2000"},
            headers=API_KEY_HEADER,
        )

    assert response.status_code == 200
    body = response.text
    assert '"event": "result"' in body
    assert "Live answer" in body
    assert '"from_memory": false' in body
    mock_stream.assert_called_once()
    mock_record.assert_called_once()
    # Records under the original query with the shortest product TTL.
    args = mock_record.call_args.args
    assert args[0] == "gaming mouse under 2000"
    assert args[2] == "2099-01-01T00:00:00+00:00"
