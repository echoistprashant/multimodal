"""Row-Preserving Markdown Table and Figure Caption Chunker."""

from typing import List
from app.grounding.bbox_merger import merge_bounding_boxes
from app.rag.chunk_schema import ChunkModality, MultimodalChunk
from app.tables.grid_schema import StructuredTable


def chunk_structured_tables(
    document_id: str,
    tables: List[StructuredTable],
    tenant_id: str = "default-tenant",
) -> List[MultimodalChunk]:
    """Serialize each table data row with its column headers so every row is self-contained."""
    chunks: List[MultimodalChunk] = []

    for table in tables:
        headers = table.headers or [f"Col {i + 1}" for i in range(table.num_cols)]
        data_rows = table.rows[1:] if (table.rows and table.rows[0].is_header_row) else table.rows

        for row in data_rows:
            pairs: List[str] = []
            for idx, cell in enumerate(row.cells):
                col_name = headers[idx] if idx < len(headers) else f"Col {idx + 1}"
                val = cell.text.strip()
                if val:
                    pairs.append(f"{col_name}: {val}")

            if not pairs:
                continue

            row_bbox = merge_bounding_boxes([c.bbox for c in row.cells]) if row.cells else table.bbox
            chunks.append(
                MultimodalChunk(
                    tenant_id=tenant_id,
                    document_id=document_id,
                    page_no=table.page_number,
                    modality=ChunkModality.TABLE_ROW,
                    text=" | ".join(pairs),
                    bbox=row_bbox,
                    metadata={"table_id": table.table_id, "row_idx": row.row_idx},
                )
            )

    return chunks


def chunk_figure_descriptions(
    document_id: str,
    page_no: int,
    figures: List[dict],
    tenant_id: str = "default-tenant",
) -> List[MultimodalChunk]:
    """Create searchable figure_desc chunks for charts, diagrams, and visual regions."""
    chunks: List[MultimodalChunk] = []
    for idx, fig in enumerate(figures):
        desc = str(fig.get("description", "")).strip()
        if not desc:
            continue
        bbox = tuple(fig.get("bbox", (0.0, 0.0, 1.0, 1.0)))
        chunks.append(
            MultimodalChunk(
                tenant_id=tenant_id,
                document_id=document_id,
                page_no=page_no,
                modality=ChunkModality.FIGURE_DESC,
                text=desc,
                bbox=bbox,  # type: ignore[arg-type]
                metadata={"figure_index": idx},
            )
        )
    return chunks
