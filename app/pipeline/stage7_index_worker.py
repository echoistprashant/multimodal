"""Stage 7 Pipeline Worker: Multimodal Chunking and Vector/Lexical Indexing."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.core.logging import get_logger
from app.layout.schema import LayoutBlock
from app.rag.chunker import UnifiedMultimodalChunker
from app.rag.vector_store import VectorIndexStore
from app.tables.grid_schema import StructuredTable

logger = get_logger("app.pipeline.stage7_index_worker")

# Shared global index store for API queries in free/local mode
_GLOBAL_VECTOR_STORE = VectorIndexStore()


def get_global_vector_store() -> VectorIndexStore:
    """Accessor for the shared in-memory vector index store."""
    return _GLOBAL_VECTOR_STORE


class Stage7IndexResult(BaseModel):
    """Summary of chunks indexed during Stage 7."""

    model_config = ConfigDict(frozen=True)

    document_id: str
    chunks_indexed: int = Field(ge=0)


class Stage7IndexWorker:
    """Chunks layout blocks, tables, and figures and indexes them for hybrid RAG."""

    def __init__(
        self,
        chunker: Optional[UnifiedMultimodalChunker] = None,
        vector_store: Optional[VectorIndexStore] = None,
    ) -> None:
        self.chunker = chunker or UnifiedMultimodalChunker()
        self.vector_store = vector_store or get_global_vector_store()

    def index_page(
        self,
        document_id: str,
        page_no: int,
        blocks: Optional[List[LayoutBlock]] = None,
        tables: Optional[List[StructuredTable]] = None,
        figures: Optional[List[dict]] = None,
        tenant_id: str = "default-tenant",
    ) -> Stage7IndexResult:
        """Chunk and index a single document page."""
        chunks = self.chunker.chunk_page(
            document_id=document_id,
            page_no=page_no,
            blocks=blocks,
            tables=tables,
            figures=figures,
            tenant_id=tenant_id,
        )
        count = self.vector_store.index_chunks(chunks)
        logger.info(f"Stage 7 indexed {count} multimodal chunks for doc={document_id} page={page_no}")
        return Stage7IndexResult(document_id=document_id, chunks_indexed=count)
