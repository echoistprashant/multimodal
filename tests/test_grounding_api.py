"""Integration tests for Phase 10 Part 10.4: Stage 5 Grounding Worker and Fields API."""

from fastapi.testclient import TestClient

from app.main import app
from app.pipeline.stage5_grounding_worker import Stage5GroundingWorker
from app.repositories.extraction_repo import ExtractionRepository

client = TestClient(app)


def test_stage5_grounding_worker_and_fields_api() -> None:
    """Verify Stage 5 grounds fields, persists bbox provenance, and serves via GET /fields."""
    ExtractionRepository().clear_cache()

    extracted_data = {
        "invoice_number": "INV-2026-77",
        "document_date": "2026-11-20",
        "vendor": {"name": "Acme Cloud Inc"},
        "total_amount": 1500.00,
        "line_items": [{"description": "Compute Cluster", "amount": 1500.0}],
    }

    pages_tokens = {
        1: [
            {"id": "t1", "text": "INV-2026-77", "bbox": (0.70, 0.05, 0.90, 0.08)},
            {"id": "t2", "text": "2026-11-20", "bbox": (0.70, 0.09, 0.85, 0.12)},
            {"id": "t3", "text": "Acme", "bbox": (0.10, 0.10, 0.18, 0.13)},
            {"id": "t4", "text": "Cloud", "bbox": (0.19, 0.10, 0.27, 0.13)},
            {"id": "t5", "text": "Inc", "bbox": (0.28, 0.10, 0.34, 0.13)},
            {"id": "t6", "text": "Compute", "bbox": (0.10, 0.35, 0.25, 0.38)},
            {"id": "t7", "text": "Cluster", "bbox": (0.26, 0.35, 0.38, 0.38)},
            {"id": "t8", "text": "$1,500.00", "bbox": (0.75, 0.60, 0.90, 0.64)},
        ]
    }

    worker = Stage5GroundingWorker()
    result = worker.process_document("doc-ground-1", extracted_data, pages_tokens)

    assert result.audit_report.grounded_count == 5
    assert result.audit_report.hallucination_rate == 0.0
    assert result.audit_report.requires_human_review is False

    # Verify API
    res = client.get("/api/v1/documents/doc-ground-1/fields")
    assert res.status_code == 200
    payload = res.json()
    assert len(payload) == 5
    by_path = {f["field_path"]: f for f in payload}
    assert by_path["vendor.name"]["bbox"] == [0.1, 0.1, 0.34, 0.13]
    assert by_path["total_amount"]["grounded"] is True

    # 404 for unknown document
    assert client.get("/api/v1/documents/unknown-doc-xyz/fields").status_code == 404
