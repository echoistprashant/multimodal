"""Unit tests for Phase 12 Part 12.3: Hybrid RRF Search, Filtering, and Reranking."""

from app.rag.chunk_schema import ChunkModality, MultimodalChunk
from app.rag.retriever import HybridRetriever
from app.rag.vector_store import VectorIndexStore


def test_hybrid_retriever_with_modality_filter() -> None:
    """Verify RRF + reranking surfaces exact table row and filters by modality."""
    store = VectorIndexStore()
    chunks = [
        MultimodalChunk(
            document_id="doc-fin",
            page_no=1,
            modality=ChunkModality.TEXT,
            text="Quarterly financial commentary on cloud infrastructure spend.",
        ),
        MultimodalChunk(
            document_id="doc-fin",
            page_no=2,
            modality=ChunkModality.TABLE_ROW,
            text="Service: GPU Cluster | Cost: $3,200.00 | Quarter: Q4-2026",
            bbox=(0.1, 0.4, 0.9, 0.45),
        ),
        MultimodalChunk(
            document_id="doc-fin",
            page_no=3,
            modality=ChunkModality.FIGURE_DESC,
            text="Line graph showing monthly GPU utilization reaching 92%.",
            bbox=(0.1, 0.2, 0.8, 0.6),
        ),
    ]
    store.index_chunks(chunks)

    retriever = HybridRetriever(vector_store=store)
    results = retriever.retrieve("What was the GPU Cluster cost in Q4-2026?", top_k=2)
    assert len(results) == 2
    assert results[0].chunk.modality == ChunkModality.TABLE_ROW
    assert "$3,200.00" in results[0].chunk.text

    # Modality-filtered search
    fig_results = retriever.retrieve("GPU utilization", modality=ChunkModality.FIGURE_DESC, top_k=2)
    assert len(fig_results) == 1
    assert fig_results[0].chunk.page_no == 3
