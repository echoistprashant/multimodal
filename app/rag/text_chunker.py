"""Layout-Aware Text Paragraph Chunker with Token Overlap."""

from typing import List
from app.layout.schema import LayoutBlock, SemanticBlockType
from app.rag.chunk_schema import ChunkModality, MultimodalChunk


def chunk_layout_blocks(
    document_id: str,
    page_no: int,
    blocks: List[LayoutBlock],
    tenant_id: str = "default-tenant",
    max_chars: int = 600,
    overlap_chars: int = 80,
) -> List[MultimodalChunk]:
    """Convert ordered LayoutBlocks into overlapping text chunks with header context."""
    chunks: List[MultimodalChunk] = []
    active_header = ""

    sorted_blocks = sorted(blocks, key=lambda b: b.reading_order)
    for block in sorted_blocks:
        txt = block.text.strip()
        if not txt:
            continue

        if block.type in (SemanticBlockType.HEADER, SemanticBlockType.SUBHEADER):
            active_header = txt

        prefix = f"[{active_header}] " if active_header and block.type == SemanticBlockType.PARAGRAPH else ""
        full_text = f"{prefix}{txt}"

        if len(full_text) <= max_chars:
            chunks.append(
                MultimodalChunk(
                    tenant_id=tenant_id,
                    document_id=document_id,
                    page_no=page_no,
                    modality=ChunkModality.TEXT,
                    text=full_text,
                    bbox=block.bbox,
                    metadata={"block_type": block.type.value, "reading_order": block.reading_order},
                )
            )
        else:
            start = 0
            while start < len(full_text):
                end = min(len(full_text), start + max_chars)
                sub_text = full_text[start:end].strip()
                if sub_text:
                    chunks.append(
                        MultimodalChunk(
                            tenant_id=tenant_id,
                            document_id=document_id,
                            page_no=page_no,
                            modality=ChunkModality.TEXT,
                            text=sub_text,
                            bbox=block.bbox,
                            metadata={"block_type": block.type.value, "split_offset": start},
                        )
                    )
                if end == len(full_text):
                    break
                start = max(start + 1, end - overlap_chars)

    return chunks
