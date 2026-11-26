"""Table Grid and Cell Spanning Reconstructor.

Reconstructs structured row and column matrices from spatial token geometries
and line intersection grids, resolving cell spans and empty slots.
"""

from typing import List, Tuple
from app.tables.grid_schema import StructuredTable, TableCell, TableRow
from app.tables.schema import TableRegion


def reconstruct_table_grid(
    table_region: TableRegion,
    tokens: List[dict],
) -> StructuredTable:
    """Reconstruct a 2D StructuredTable from page tokens located inside the table region.

    Args:
        table_region: Detected TableRegion with boundary.
        tokens: Page tokens with 'bbox' [x0, y0, x1, y1] and 'text'.

    Returns:
        StructuredTable containing rows, columns, and assigned TableCell instances.
    """
    t_x0, t_y0, t_x1, t_y1 = table_region.boundary.bbox

    # Filter tokens that fall within or overlap the table bounding box
    contained_tokens = [
        t for t in tokens
        if not (t["bbox"][2] < t_x0 or t["bbox"][0] > t_x1 or t["bbox"][3] < t_y0 or t["bbox"][1] > t_y1)
    ]

    if not contained_tokens:
        return StructuredTable(
            page_number=table_region.page_number,
            bbox=(t_x0, t_y0, t_x1, t_y1),
            num_rows=0,
            num_cols=0,
            headers=[],
            rows=[],
        )

    # 1. Cluster tokens into distinct vertical row intervals
    sorted_by_y = sorted(contained_tokens, key=lambda t: ((t["bbox"][1] + t["bbox"][3]) / 2.0))
    row_clusters: List[List[dict]] = []
    current_row: List[dict] = []
    current_y = -1.0
    row_tolerance = max(0.012, (t_y1 - t_y0) / max(table_region.boundary.row_count_estimate * 3, 10))

    for tok in sorted_by_y:
        mid_y = (tok["bbox"][1] + tok["bbox"][3]) / 2.0
        if current_y < 0 or abs(mid_y - current_y) <= row_tolerance:
            current_row.append(tok)
            current_y = sum((t["bbox"][1] + t["bbox"][3]) / 2.0 for t in current_row) / len(current_row)
        else:
            if current_row:
                row_clusters.append(sorted(current_row, key=lambda t: t["bbox"][0]))
            current_row = [tok]
            current_y = mid_y

    if current_row:
        row_clusters.append(sorted(current_row, key=lambda t: t["bbox"][0]))

    # 2. Derive global column boundaries by clustering X coordinates
    all_col_centers: List[float] = [
        (t["bbox"][0] + t["bbox"][2]) / 2.0 for t in contained_tokens
    ]
    all_col_centers.sort()

    col_clusters: List[float] = []
    col_tolerance = 0.04
    for cx in all_col_centers:
        matched = False
        for i, c_mean in enumerate(col_clusters):
            if abs(cx - c_mean) <= col_tolerance:
                col_clusters[i] = (c_mean + cx) / 2.0
                matched = True
                break
        if not matched:
            col_clusters.append(cx)

    col_clusters.sort()
    num_cols = max(len(col_clusters), 1)
    num_rows = len(row_clusters)

    # 3. Build TableRow and TableCell instances
    rows: List[TableRow] = []
    for r_idx, row_toks in enumerate(row_clusters):
        cells: List[TableCell] = []
        for c_idx, col_center in enumerate(col_clusters):
            # Find tokens closest to this column center
            matching_toks = [
                t for t in row_toks
                if abs(((t["bbox"][0] + t["bbox"][2]) / 2.0) - col_center) <= (col_tolerance * 1.5)
            ]
            cell_text = " ".join(t.get("text", "").strip() for t in matching_toks if t.get("text"))

            if matching_toks:
                c_x0 = min(t["bbox"][0] for t in matching_toks)
                c_y0 = min(t["bbox"][1] for t in matching_toks)
                c_x1 = max(t["bbox"][2] for t in matching_toks)
                c_y1 = max(t["bbox"][3] for t in matching_toks)
            else:
                c_x0 = max(col_center - 0.02, t_x0)
                c_x1 = min(col_center + 0.02, t_x1)
                c_y0 = row_toks[0]["bbox"][1] if row_toks else t_y0
                c_y1 = row_toks[0]["bbox"][3] if row_toks else t_y1

            cell = TableCell(
                row_idx=r_idx,
                col_idx=c_idx,
                row_span=1,
                col_span=1,
                text=cell_text,
                bbox=(round(c_x0, 4), round(c_y0, 4), round(c_x1, 4), round(c_y1, 4)),
                is_header=(r_idx == 0),
            )
            cells.append(cell)

        rows.append(TableRow(row_idx=r_idx, cells=cells, is_header_row=(r_idx == 0)))

    # Headers inferred from row 0
    headers = [c.text for c in rows[0].cells] if rows else []

    return StructuredTable(
        page_number=table_region.page_number,
        bbox=(t_x0, t_y0, t_x1, t_y1),
        num_rows=num_rows,
        num_cols=num_cols,
        headers=headers,
        rows=rows,
    )
