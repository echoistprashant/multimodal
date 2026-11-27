"""Unit tests for Phase 12 Part 12.2: Local Embeddings, Vector Search, and BM25."""

from app.rag.bm25 import BM25Scorer
from app.rag.chunk_schema import ChunkModality, MultimodalChunk
from app.rag.local_embedder import LocalDenseEmbedder
from app.rag.vector_store import VectorIndexStore


def test_local_embedder_and_vector_store() -> None:
    """Verify deterministic L2 embeddings and cosine similarity retrieval."""
    embedder = LocalDenseEmbedder(dimension=128)
    vecs = embedder.embed_texts(["cloud gpu cluster hosting", "medical hospital bill"])
    assert len(vecs) == 2
    assert len(vecs[0]) == 128

    store = VectorIndexStore(embedder=embedder)
    c1 = MultimodalChunk(
        tenant_id="tenant-a",
        document_id="doc-1",
        page_no=1,
        modality=ChunkModality.TEXT,
        text="Dedicated cloud gpu cluster hosting charges",
    )
    c2 = MultimodalChunk(
        tenant_id="tenant-a",
        document_id="doc-2",
        page_no=1,
        modality=ChunkModality.TEXT,
        text="Patient discharged from hospital clinic",
    )
    c_other_tenant = MultimodalChunk(
        tenant_id="tenant-b",
        document_id="doc-3",
        page_no=1,
        modality=ChunkModality.TEXT,
        text="Dedicated cloud gpu cluster secret",
    )
    store.index_chunks([c1, c2, c_other_tenant])

    hits = store.search_dense("cloud gpu cluster", tenant_id="tenant-a", top_k=2)
    assert len(hits) == 2
    assert hits[0].chunk.chunk_id == c1.chunk_id
    # Tenant isolation check
    assert all(h.chunk.tenant_id == "tenant-a" for h in hits)


def test_bm25_exact_identifier_match() -> None:
    """Verify BM25 accurately ranks exact invoice numbers and SKU codes."""
    chunks = [
        MultimodalChunk(document_id="d1", page_no=1, modality=ChunkModality.TEXT, text="Invoice INV-99412 for server rack"),
        MultimodalChunk(document_id="d2", page_no=1, modality=ChunkModality.TEXT, text="General office stationery supplies"),
    ]
    hits = BM25Scorer().search("INV-99412", chunks, top_k=2)
    assert len(hits) == 1
    assert hits[0].chunk.document_id == "d1"
    assert hits[0].score > 0.0
