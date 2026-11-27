"""Multimodal Hybrid Search & RAG Q&A API Endpoints."""

from typing import List
from fastapi import APIRouter

from app.pipeline.stage7_index_worker import get_global_vector_store
from app.rag.embed_schema import VectorSearchResult
from app.rag.qa_engine import RAGAnswerGenerator
from app.rag.qa_schema import RAGAnswerResponse, RAGQueryRequest
from app.rag.retriever import HybridRetriever

router = APIRouter(prefix="/api/v1/rag", tags=["Multimodal RAG"])


@router.post(
    "/search",
    response_model=List[VectorSearchResult],
    summary="Hybrid dense + BM25 multimodal document search",
)
def hybrid_search(request: RAGQueryRequest) -> List[VectorSearchResult]:
    """Search indexed text, table rows, and figure captions with tenant isolation."""
    retriever = HybridRetriever(vector_store=get_global_vector_store())
    return retriever.retrieve(
        query=request.query,
        tenant_id=request.tenant_id,
        top_k=request.top_k,
        document_id=request.document_id,
        modality=request.modality,
    )


@router.post(
    "/query",
    response_model=RAGAnswerResponse,
    summary="Grounded Multimodal RAG Question Answering with Visual Citations",
)
def rag_query(request: RAGQueryRequest) -> RAGAnswerResponse:
    """Answer questions across indexed documents with page numbers and [x0, y0, x1, y1] citations."""
    retriever = HybridRetriever(vector_store=get_global_vector_store())
    engine = RAGAnswerGenerator(retriever=retriever)
    return engine.answer_query(request)
