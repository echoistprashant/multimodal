"""End-to-End Integration Test for Phase 13 Part 13.3: MasterPipelineOrchestrator & Process API."""

from fastapi.testclient import TestClient

from app.main import app
from app.pipeline.stage7_index_worker import get_global_vector_store
from app.repositories.extraction_repo import ExtractionRepository
from app.repositories.review_repo import ReviewQueueRepository
from app.repositories.routing_repo import RoutingRepository

client = TestClient(app)


def test_full_end_to_end_pipeline_invoice_to_rag() -> None:
    """Verify invoice flows through Triage -> Layout -> Extraction -> Grounding -> Validation -> RAG."""
    get_global_vector_store().clear()
    ExtractionRepository().clear_cache()
    ReviewQueueRepository().clear_cache()
    RoutingRepository().clear_cache()

    tokens = [
        {"id": "t1", "text": "TAX INVOICE #9955", "bbox": (0.10, 0.05, 0.90, 0.10)},
        {"id": "t2", "text": "Vendor: Acme Logistics Corp", "bbox": (0.10, 0.14, 0.60, 0.18)},
        {"id": "t3", "text": "Service Item", "bbox": (0.10, 0.30, 0.45, 0.34)},
        {"id": "t4", "text": "Amount", "bbox": (0.70, 0.30, 0.88, 0.34)},
        {"id": "t5", "text": "Enterprise Support", "bbox": (0.10, 0.38, 0.45, 0.42)},
        {"id": "t6", "text": "$1,200.00", "bbox": (0.70, 0.38, 0.88, 0.42)},
        {"id": "t7", "text": "Total Amount: $1,200.00", "bbox": (0.50, 0.65, 0.90, 0.70)},
    ]

    res = client.post(
        "/api/v1/documents/doc-master-1/process",
        json={
            "pages": [{"page_no": 1, "tokens": tokens}],
            "config": {"tenant_id": "tenant-e2e", "enable_rag_indexing": True},
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["document_id"] == "doc-master-1"
    assert body["doc_type"] == "invoice"
    assert body["chunks_indexed"] >= 1
    assert len(body["stage_traces"]) == 6
    assert body["routing_report"]["total_pages"] == 1

    # Verify fields API populated
    fields_res = client.get("/api/v1/documents/doc-master-1/fields")
    assert fields_res.status_code == 200
    assert len(fields_res.json()) >= 1

    # Verify RAG Q&A works immediately on processed document
    rag_res = client.post(
        "/api/v1/rag/query",
        json={"query": "Enterprise Support $1,200.00", "tenant_id": "tenant-e2e", "top_k": 2},
    )
    assert rag_res.status_code == 200
    assert len(rag_res.json()["citations"]) >= 1
