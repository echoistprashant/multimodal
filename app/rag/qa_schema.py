"""Visual Citation Q&A Request and Response Schemas."""

from typing import List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

from app.rag.chunk_schema import ChunkModality


class VisualCitation(BaseModel):
    """Grounded citation linking a RAG answer claim to a document page and bbox."""

    model_config = ConfigDict(frozen=True)

    document_id: str
    page_no: int = Field(ge=1)
    bbox: Tuple[float, float, float, float]
    modality: ChunkModality
    excerpt: str
    relevance_score: float


class RAGQueryRequest(BaseModel):
    """Query payload for multimodal RAG Q&A and hybrid search."""

    model_config = ConfigDict(frozen=True)

    query: str = Field(..., min_length=2)
    tenant_id: str = Field(default="default-tenant")
    document_id: Optional[str] = Field(default=None)
    modality: Optional[ChunkModality] = Field(default=None)
    top_k: int = Field(default=5, ge=1, le=20)


class RAGAnswerResponse(BaseModel):
    """Grounded natural language answer with verifiable page/bbox citations."""

    model_config = ConfigDict(frozen=True)

    query: str
    answer: str
    citations: List[VisualCitation] = Field(default_factory=list)
    retrieved_chunks_count: int = Field(ge=0)
