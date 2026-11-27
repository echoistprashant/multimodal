"""Vector Index Store with Cosine Similarity and Tenant Isolation."""

import math
from typing import Dict, List, Optional, Tuple

from app.rag.chunk_schema import ChunkModality, MultimodalChunk
from app.rag.embed_schema import EmbeddingProviderProtocol, VectorSearchResult
from app.rag.local_embedder import LocalDenseEmbedder


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two equal-length float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    n1 = math.sqrt(sum(a * a for a in v1))
    n2 = math.sqrt(sum(b * b for b in v2))
    if n1 == 0.0 or n2 == 0.0:
        return 0.0
    return round(dot / (n1 * n2), 6)


class VectorIndexStore:
    """In-memory vector store mirroring pgvector IndexItem schema semantics."""

    def __init__(self, embedder: Optional[EmbeddingProviderProtocol] = None) -> None:
        self.embedder = embedder or LocalDenseEmbedder()
        self._records: Dict[str, Tuple[MultimodalChunk, List[float]]] = {}

    def index_chunks(self, chunks: List[MultimodalChunk]) -> int:
        """Embed and store multimodal chunks."""
        if not chunks:
            return 0
        vectors = self.embedder.embed_texts([c.text for c in chunks])
        for chunk, vec in zip(chunks, vectors):
            self._records[chunk.chunk_id] = (chunk, vec)
        return len(chunks)

    def search_dense(
        self,
        query: str,
        tenant_id: str = "default-tenant",
        top_k: int = 5,
        document_id: Optional[str] = None,
        modality: Optional[ChunkModality] = None,
    ) -> List[VectorSearchResult]:
        """Retrieve top-K chunks ranked by dense cosine similarity."""
        query_vec = self.embedder.embed_texts([query])[0]
        scored: List[VectorSearchResult] = []

        for chunk, vec in self._records.values():
            if chunk.tenant_id != tenant_id:
                continue
            if document_id and chunk.document_id != document_id:
                continue
            if modality and chunk.modality != modality:
                continue
            sim = cosine_similarity(query_vec, vec)
            scored.append(VectorSearchResult(chunk=chunk, score=sim, source="dense"))

        scored.sort(key=lambda r: -r.score)
        return scored[:top_k]

    def get_tenant_chunks(
        self,
        tenant_id: str = "default-tenant",
        document_id: Optional[str] = None,
        modality: Optional[ChunkModality] = None,
    ) -> List[MultimodalChunk]:
        """Return filtered chunks for lexical scoring."""
        return [
            c for c, _ in self._records.values()
            if c.tenant_id == tenant_id
            and (document_id is None or c.document_id == document_id)
            and (modality is None or c.modality == modality)
        ]

    def clear(self) -> None:
        """Clear all indexed chunks."""
        self._records.clear()
