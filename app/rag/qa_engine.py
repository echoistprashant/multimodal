"""Grounded Multimodal RAG Answer Generator with Visual Citations."""

from typing import List, Optional
from app.rag.qa_schema import RAGAnswerResponse, RAGQueryRequest, VisualCitation
from app.rag.retriever import HybridRetriever


class RAGAnswerGenerator:
    """Synthesizes grounded answers from retrieved multimodal chunks with visual bbox citations."""

    def __init__(self, retriever: Optional[HybridRetriever] = None) -> None:
        self.retriever = retriever or HybridRetriever()

    def answer_query(self, request: RAGQueryRequest) -> RAGAnswerResponse:
        """Retrieve relevant multimodal chunks and synthesize a cited response."""
        hits = self.retriever.retrieve(
            query=request.query,
            tenant_id=request.tenant_id,
            top_k=request.top_k,
            document_id=request.document_id,
            modality=request.modality,
        )

        if not hits:
            return RAGAnswerResponse(
                query=request.query,
                answer="No relevant evidence found in the indexed documents for this query.",
                citations=[],
                retrieved_chunks_count=0,
            )

        citations: List[VisualCitation] = [
            VisualCitation(
                document_id=h.chunk.document_id,
                page_no=h.chunk.page_no,
                bbox=h.chunk.bbox,
                modality=h.chunk.modality,
                excerpt=h.chunk.text[:240],
                relevance_score=h.score,
            )
            for h in hits
        ]

        # Synthesize deterministic grounded summary citing top evidence spans
        top = hits[0]
        evidence_lines = [
            f"[{i + 1}] (Page {c.page_no}, {c.modality.value}): {c.excerpt}"
            for i, c in enumerate(citations[:3])
        ]
        answer = (
            f"Based on document evidence (top match on Page {top.chunk.page_no}): "
            f"{top.chunk.text}\n\nSources:\n" + "\n".join(evidence_lines)
        )

        return RAGAnswerResponse(
            query=request.query,
            answer=answer,
            citations=citations,
            retrieved_chunks_count=len(hits),
        )
