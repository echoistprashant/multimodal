"""System Integrity, OpenAPI Schema, and Deployment Readiness Tests."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_system_info_and_openapi_integrity() -> None:
    """Verify /api/v1/system/info and OpenAPI schema expose all 13 phases' endpoints."""
    info_res = client.get("/api/v1/system/info")
    assert info_res.status_code == 200
    info = info_res.json()
    assert info["completed_phases"] == 13
    assert len(info["pipeline_stages"]) == 6

    openapi_res = client.get("/api/v1/openapi.json")
    assert openapi_res.status_code == 200
    paths = openapi_res.json()["paths"]
    expected_paths = [
        "/health",
        "/ready",
        "/api/v1/system/info",
        "/api/v1/documents",
        "/api/v1/documents/{document_id}/routing",
        "/api/v1/documents/{document_id}/fields",
        "/api/v1/documents/{document_id}/process",
        "/api/v1/schemas",
        "/api/v1/reviews",
        "/api/v1/rag/search",
        "/api/v1/rag/query",
        "/api/v1/metrics",
    ]
    for p in expected_paths:
        assert p in paths, f"Missing expected API path: {p}"
