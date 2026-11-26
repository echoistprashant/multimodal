"""Semantic HTML Layout Serializer with Grounding Coordinates.

Converts segmented document structures and reconstructed table grids into valid HTML5,
embedding normalized bounding box coordinates for frontend visual overlays and audit grounding.
"""

import html
from typing import List, Optional
from app.layout.schema import LayoutBlock, SemanticBlockType
from app.tables.grid_schema import StructuredTable


def table_to_html(table: StructuredTable, include_coordinates: bool = True) -> str:
    """Render a StructuredTable into semantic HTML table markup."""
    if not table.rows:
        return ""

    t_bbox_attr = f' data-bbox="{table.bbox[0]},{table.bbox[1]},{table.bbox[2]},{table.bbox[3]}"' if include_coordinates else ""
    lines: List[str] = [f"<table{t_bbox_attr}>"]

    # Header Row
    if table.headers:
        lines.append("  <thead>\n    <tr>")
        for h in table.headers:
            lines.append(f"      <th>{html.escape(h)}</th>")
        lines.append("    </tr>\n  </thead>")

    # Body Rows
    lines.append("  <tbody>")
    data_rows = table.rows[1:] if (table.rows and table.rows[0].is_header_row) else table.rows
    for row in data_rows:
        lines.append("    <tr>")
        for cell in row.cells:
            c_bbox = f' data-bbox="{cell.bbox[0]},{cell.bbox[1]},{cell.bbox[2]},{cell.bbox[3]}"' if include_coordinates else ""
            lines.append(f"      <td{c_bbox}>{html.escape(cell.text)}</td>")
        lines.append("    </tr>")
    lines.append("  </tbody>")
    lines.append("</table>")

    return "\n".join(lines)


def serialize_blocks_to_html(
    blocks: List[LayoutBlock],
    tables: Optional[List[StructuredTable]] = None,
    include_coordinates: bool = True,
) -> str:
    """Serialize layout blocks and tables into valid HTML."""
    sorted_blocks = sorted(blocks, key=lambda b: b.reading_order)
    html_elements: List[str] = []

    for block in sorted_blocks:
        text = html.escape(block.text.strip())
        if not text:
            continue

        bbox_str = f' data-bbox="{block.bbox[0]},{block.bbox[1]},{block.bbox[2]},{block.bbox[3]}"' if include_coordinates else ""

        if block.type == SemanticBlockType.HEADER:
            html_elements.append(f"<h1{bbox_str}>{text}</h1>")
        elif block.type == SemanticBlockType.SUBHEADER:
            html_elements.append(f"<h2{bbox_str}>{text}</h2>")
        elif block.type == SemanticBlockType.LIST_ITEM:
            html_elements.append(f"<ul><li{bbox_str}>{text}</li></ul>")
        elif block.type == SemanticBlockType.FOOTER:
            html_elements.append(f"<footer{bbox_str}><small>{text}</small></footer>")
        else:
            html_elements.append(f"<p{bbox_str}>{text}</p>")

    if tables:
        for t in tables:
            t_html = table_to_html(t, include_coordinates=include_coordinates)
            if t_html:
                html_elements.append(t_html)

    return "\n".join(html_elements)
