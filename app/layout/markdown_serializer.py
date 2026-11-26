"""Markdown Layout-Aware Serializer.

Transforms structured document layout blocks and reconstructed table matrices
into standardized GitHub Flavored Markdown (GFM) suitable for LLM context windows.
"""

from typing import List, Optional
from app.layout.schema import LayoutBlock, SemanticBlockType
from app.tables.grid_schema import StructuredTable


def table_to_markdown(table: StructuredTable) -> str:
    """Convert a StructuredTable into GFM Markdown table representation."""
    if not table.rows:
        return ""

    lines: List[str] = []

    # 1. Header row
    headers = table.headers or [f"Col {i + 1}" for i in range(table.num_cols)]
    header_line = "| " + " | ".join(h.replace("|", "\\|") for h in headers) + " |"
    divider_line = "| " + " | ".join("---" for _ in headers) + " |"

    lines.append(header_line)
    lines.append(divider_line)

    # 2. Data rows
    # Skip row 0 if it was used as the header
    data_rows = table.rows[1:] if (table.rows and table.rows[0].is_header_row) else table.rows

    for row in data_rows:
        cell_texts = [c.text.replace("|", "\\|").replace("\n", " ") for c in row.cells]
        # Pad row if fewer cells than headers
        while len(cell_texts) < len(headers):
            cell_texts.append("")
        row_line = "| " + " | ".join(cell_texts[:len(headers)]) + " |"
        lines.append(row_line)

    return "\n".join(lines)


def serialize_blocks_to_markdown(
    blocks: List[LayoutBlock],
    tables: Optional[List[StructuredTable]] = None,
) -> str:
    """Serialize layout blocks and embedded tables into ordered Markdown text.

    Args:
        blocks: List of LayoutBlocks sorted in reading order.
        tables: Optional list of StructuredTables to insert at appropriate positions.

    Returns:
        Structured Markdown string.
    """
    sorted_blocks = sorted(blocks, key=lambda b: b.reading_order)
    md_parts: List[str] = []

    for block in sorted_blocks:
        text = block.text.strip()
        if not text:
            continue

        if block.type == SemanticBlockType.HEADER:
            md_parts.append(f"# {text}")
        elif block.type == SemanticBlockType.SUBHEADER:
            md_parts.append(f"## {text}")
        elif block.type == SemanticBlockType.LIST_ITEM:
            md_parts.append(f"- {text}")
        elif block.type == SemanticBlockType.FOOTER:
            md_parts.append(f"---\n*{text}*")
        else:
            md_parts.append(text)

    # Append any tables
    if tables:
        for t in tables:
            t_md = table_to_markdown(t)
            if t_md:
                md_parts.append(t_md)

    return "\n\n".join(md_parts)
