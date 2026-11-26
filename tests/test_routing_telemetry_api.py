"""Integration tests for Phase 6 Part 6.4: Routing Telemetry Repository and API Endpoints."""

import uuid
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.routing_repo import RoutingRepository
from app.routing.cost_estimator import estimate_route_cost
from app.routing.schema import RouteDecision, RouteType
from app.routing.telemetry import RoutingTelemetryAccumulator

client = TestClient(app)


def test_get_routing_telemetry_not_found() -> None:
    """Verify querying non-existent document routing report returns 404."""
    non_existent_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/documents/{non_existent_id}/routing")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_routing_telemetry_success() -> None:
    """Verify saved routing telemetry report is correctly served via HTTP API."""
    doc_id = str(uuid.uuid4())
    accumulator = RoutingTelemetryAccumulator(document_id=doc_id)

    # Record 2 native pages and 1 OCR page
    accumulator.record_decision(
        page_number=1,
        decision=RouteDecision(
            route=RouteType.NATIVE,
            confidence=0.95,
            reason="Clean native PDF",
            cost_estimate=estimate_route_cost(RouteType.NATIVE),
            text_health_score=0.92,
            visual_complexity_score=0.08,
        ),
    )
    accumulator.record_decision(
        page_number=2,
        decision=RouteDecision(
            route=RouteType.NATIVE,
            confidence=0.94,
            reason="Clean native PDF",
            cost_estimate=estimate_route_cost(RouteType.NATIVE),
            text_health_score=0.91,
            visual_complexity_score=0.10,
        ),
    )
    accumulator.record_decision(
        page_number=3,
        decision=RouteDecision(
            route=RouteType.OCR,
            confidence=0.88,
            reason="Low text layer health",
            cost_estimate=estimate_route_cost(RouteType.OCR),
            text_health_score=0.20,
            visual_complexity_score=0.30,
        ),
    )

    report = accumulator.generate_report()
    repo = RoutingRepository()
    repo.save_report(report)

    # Query via API
    response = client.get(f"/api/v1/documents/{doc_id}/routing")
    assert response.status_code == 200

    payload = response.json()
    assert payload["document_id"] == doc_id
    assert payload["total_pages"] == 3
    assert payload["native_page_count"] == 2
    assert payload["ocr_page_count"] == 1
    assert payload["vlm_page_count"] == 0
    assert payload["total_cost_usd"] == 0.0
    assert payload["unoptimized_cost_usd"] > 0.0
    assert payload["savings_percentage"] == 100.0
    assert "1" in payload["page_decisions"]
