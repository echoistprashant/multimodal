"""Embedding Provider Protocol and Vector Search Result Schemas."""

from typing import List, Protocol, runtime_checkable
from pydantic import BaseModel, ConfigDict, Field

from app.rag.chunk_schema import MultimodalChunk


class VectorSearchResult(BaseModel):
    """Ranked search hit returned by dense, lexical, or hybrid retrieval."""

    model_config = ConfigDict(frozen=True)

    chunk: MultimodalChunk
    score: float = Field(..., description="Similarity or relevance score.")
    source: str = Field(default="hybrid", description="'dense', 'bm25', or 'hybrid'.")


@runtime_checkable
class EmbeddingProviderProtocol(Protocol):
    """Protocol for text and multimodal embedding generators."""

    @property
    def dimension(self) -> int:
        ...

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        ...
