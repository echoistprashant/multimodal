"""Unified Multimodal Document Chunker."""

from typing import List, Optional
from app.layout.schema import LayoutBlock
from app.rag.chunk_schema import MultimodalChunk
from app.rag.table_chunker import chunk_figure_descriptions, chunk_structured_tables
from app.rag.text_chunker import chunk_layout_blocks
from app.tables.grid_schema import StructuredTable


class UnifiedMultimodalChunker:
    """Combines text blocks, structured table rows, and figure captions into RAG chunks."""

    def __init__(self, max_chars: int = 600, overlap_chars: int = 80) -> None:
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def chunk_page(
        self,
        document_id: str,
        page_no: int,
        blocks: Optional[List[LayoutBlock]] = None,
        tables: Optional[List[StructuredTable]] = None,
        figures: Optional[List[dict]] = None,
        tenant_id: str = "default-tenant",
    ) -> List[MultimodalChunk]:
        """Produce all multimodal chunks for a single document page."""
        chunks: List[MultimodalChunk] = []

        if blocks:
            chunks.extend(
                chunk_layout_blocks(
                    document_id=document_id,
                    page_no=page_no,
                    blocks=blocks,
                    tenant_id=tenant_id,
                    max_chars=self.max_chars,
                    overlap_chars=self.overlap_chars,
                )
            )

        if tables:
            chunks.extend(chunk_structured_tables(document_id=document_id, tables=tables, tenant_id=tenant_id))

        if figures:
            chunks.extend(
                chunk_figure_descriptions(
                    document_id=document_id,
                    page_no=page_no,
                    figures=figures,
                    tenant_id=tenant_id,
                )
            )

        return chunks
