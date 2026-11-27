"""Unit tests for Phase 13 Part 13.2: Observability Metrics, Tracer, and API."""

from fastapi.testclient import TestClient

from app.main import app
from app.observability.metrics import MetricsCollector
from app.observability.tracer import PipelineStageTracer

client = TestClient(app)


def test_metrics_tracer_and_api() -> None:
    """Verify PipelineStageTracer records spans and GET /api/v1/metrics exposes them."""
    MetricsCollector.get_instance().reset()

    tracer = PipelineStageTracer(document_id="doc-obs-1")
    with tracer.trace_stage("layout_analysis"):
        _ = sum(range(1000))
    with tracer.trace_stage("extraction"):
        _ = sum(range(1000))

    assert len(tracer.spans) == 2
    assert tracer.spans[0].stage_name == "layout_analysis"

    res = client.get("/api/v1/metrics")
    assert res.status_code == 200
    data = res.json()
    assert data["counters"]["stage.layout_analysis.ok"] == 1
    assert data["counters"]["stage.extraction.ok"] == 1
    assert "layout_analysis" in data["latencies"]
