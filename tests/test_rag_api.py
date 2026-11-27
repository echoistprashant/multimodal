"""Integration tests for Phase 12 Part 12.4: Stage 7 Indexing Worker and RAG API."""

from fastapi.testclient import TestClient

from app.layout.schema import LayoutBlock, SemanticBlockType
from app.main import app
from app.pipeline.stage7_index_worker import Stage7IndexWorker, get_global_vector_store
from app.tables.grid_schema import StructuredTable, TableCell, TableRow

client = TestClient(app)


def test_stage7_index_and_rag_api() -> None:
    """Verify Stage 7 indexes multimodal chunks and /api/v1/rag/query returns visual citations."""
    get_global_vector_store().clear()

    blocks = [
        LayoutBlock(
            type=SemanticBlockType.HEADER,
            bbox=(0.1, 0.05, 0.9, 0.10),
            reading_order=0,
            text="Annual Infrastructure Audit 2026",
        ),
        LayoutBlock(
            type=SemanticBlockType.PARAGRAPH,
            bbox=(0.1, 0.12, 0.9, 0.22),
            reading_order=1,
            text="Total annual cloud spend decreased by 18% due to multi-tier routing.",
        ),
    ]
    tables = [
        StructuredTable(
            page_number=1,
            bbox=(0.1, 0.3, 0.9, 0.5),
            num_rows=2,
            num_cols=2,
            headers=["Tier", "Savings"],
            rows=[
                TableRow(row_idx=0, is_header_row=True, cells=[
                    TableCell(row_idx=0, col_idx=0, text="Tier", bbox=(0.1, 0.3, 0.4, 0.35), is_header=True),
                    TableCell(row_idx=0, col_idx=1, text="Savings", bbox=(0.5, 0.3, 0.9, 0.35), is_header=True),
                ]),
                TableRow(row_idx=1, is_header_row=False, cells=[
                    TableCell(row_idx=1, col_idx=0, text="Native PDF", bbox=(0.1, 0.36, 0.4, 0.42)),
                    TableCell(row_idx=1, col_idx=1, text="$42,500", bbox=(0.5, 0.36, 0.9, 0.42)),
                ]),
            ],
        )
    ]

    worker = Stage7IndexWorker()
    idx_res = worker.index_page("doc-audit-2026", page_no=1, blocks=blocks, tables=tables)
    assert idx_res.chunks_indexed == 3

    # 1. Hybrid Search
    search_res = client.post(
        "/api/v1/rag/search",
        json={"query": "Native PDF savings", "top_k": 2},
    )
    assert search_res.status_code == 200
    assert len(search_res.json()) >= 1

    # 2. RAG Q&A with Visual Citations
    qa_res = client.post(
        "/api/v1/rag/query",
        json={"query": "How much savings came from Native PDF?", "top_k": 3},
    )
    assert qa_res.status_code == 200
    body = qa_res.json()
    assert "$42,500" in body["answer"]
    assert len(body["citations"]) >= 1
    assert body["citations"][0]["page_no"] == 1
    assert len(body["citations"][0]["bbox"]) == 4
