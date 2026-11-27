"""Hybrid Retriever Orchestrating Dense, BM25, RRF Fusion, and Reranking."""

from typing import List, Optional
from app.rag.bm25 import BM25Scorer
from app.rag.chunk_schema import ChunkModality
from app.rag.embed_schema import VectorSearchResult
from app.rag.reranker import rerank_results
from app.rag.rrf import reciprocal_rank_fusion
from app.rag.vector_store import VectorIndexStore


class HybridRetriever:
    """Tenant-scoped multimodal hybrid search engine."""

    def __init__(
        self,
        vector_store: Optional[VectorIndexStore] = None,
        bm25_scorer: Optional[BM25Scorer] = None,
    ) -> None:
        self.vector_store = vector_store or VectorIndexStore()
        self.bm25_scorer = bm25_scorer or BM25Scorer()

    def retrieve(
        self,
        query: str,
        tenant_id: str = "default-tenant",
        top_k: int = 5,
        document_id: Optional[str] = None,
        modality: Optional[ChunkModality] = None,
    ) -> List[VectorSearchResult]:
        """Run dense + BM25 search, fuse via RRF, and rerank top candidates."""
        candidate_pool_k = max(top_k * 3, 15)

        dense_hits = self.vector_store.search_dense(
            query=query,
            tenant_id=tenant_id,
            top_k=candidate_pool_k,
            document_id=document_id,
            modality=modality,
        )

        tenant_chunks = self.vector_store.get_tenant_chunks(
            tenant_id=tenant_id,
            document_id=document_id,
            modality=modality,
        )
        bm25_hits = self.bm25_scorer.search(query=query, chunks=tenant_chunks, top_k=candidate_pool_k)

        fused = reciprocal_rank_fusion(dense_hits, bm25_hits)
        return rerank_results(query=query, candidates=fused, top_k=top_k)
