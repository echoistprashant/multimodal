"""Unit tests for Phase 12 Part 12.1: Multimodal Chunking Engine."""

from app.layout.schema import LayoutBlock, SemanticBlockType
from app.rag.chunk_schema import ChunkModality
from app.rag.chunker import UnifiedMultimodalChunker
from app.tables.grid_schema import StructuredTable, TableCell, TableRow


def test_unified_multimodal_chunker() -> None:
    """Verify text blocks, table rows, and figure captions chunk with preserved bbox."""
    blocks = [
        LayoutBlock(type=SemanticBlockType.HEADER, bbox=(0.1, 0.05, 0.9, 0.1), reading_order=0, text="Q4 Summary"),
        LayoutBlock(type=SemanticBlockType.PARAGRAPH, bbox=(0.1, 0.12, 0.9, 0.2), reading_order=1, text="Revenue grew 25% YoY."),
    ]
    tables = [
        StructuredTable(
            page_number=1,
            bbox=(0.1, 0.3, 0.9, 0.5),
            num_rows=2,
            num_cols=2,
            headers=["Quarter", "Revenue"],
            rows=[
                TableRow(row_idx=0, is_header_row=True, cells=[
                    TableCell(row_idx=0, col_idx=0, text="Quarter", bbox=(0.1, 0.3, 0.4, 0.35), is_header=True),
                    TableCell(row_idx=0, col_idx=1, text="Revenue", bbox=(0.5, 0.3, 0.9, 0.35), is_header=True),
                ]),
                TableRow(row_idx=1, is_header_row=False, cells=[
                    TableCell(row_idx=1, col_idx=0, text="Q4-2026", bbox=(0.1, 0.36, 0.4, 0.42)),
                    TableCell(row_idx=1, col_idx=1, text="$4.2M", bbox=(0.5, 0.36, 0.9, 0.42)),
                ]),
            ],
        )
    ]
    figures = [{"description": "Bar chart showing Q1 to Q4 upward revenue trajectory.", "bbox": (0.1, 0.55, 0.9, 0.85)}]

    chunker = UnifiedMultimodalChunker()
    chunks = chunker.chunk_page("doc-rag-1", page_no=1, blocks=blocks, tables=tables, figures=figures)

    assert len(chunks) == 4
    modalities = [c.modality for c in chunks]
    assert modalities.count(ChunkModality.TEXT) == 2
    assert modalities.count(ChunkModality.TABLE_ROW) == 1
    assert modalities.count(ChunkModality.FIGURE_DESC) == 1

    # Header context prepended to paragraph
    assert "[Q4 Summary] Revenue grew 25% YoY." in chunks[1].text
    # Table row preserves column headers
    assert chunks[2].text == "Quarter: Q4-2026 | Revenue: $4.2M"
