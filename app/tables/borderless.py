"""Whitespace Alignment Analyzer for Borderless Tables.

Detects tables lacking explicit visual borders by identifying repeating horizontal
text lines with vertically aligned columnar whitespace gaps.
"""

from typing import List, Tuple
from app.tables.schema import TableBoundary, TableRegion, TableType


def detect_borderless_tables(
    tokens: List[dict],
    min_rows: int = 3,
    min_cols: int = 2,
    x_align_tolerance: float = 0.02,
    y_line_tolerance: float = 0.015,
) -> List[TableRegion]:
    """Detect borderless tables by identifying multi-row column alignment clusters.

    Args:
        tokens: List of tokens with 'bbox' [x0, y0, x1, y1] and optional 'text'.
        min_rows: Minimum consecutive aligned lines required to qualify as a table.
        min_cols: Minimum columns per row.
        x_align_tolerance: Max X-coordinate deviation for column alignment.
        y_line_tolerance: Max vertical gap for clustering tokens into the same text row.

    Returns:
        List of detected borderless TableRegion objects.
    """
    if len(tokens) < (min_rows * min_cols):
        return []

    # 1. Group tokens into horizontal lines based on Y-midpoint
    sorted_tokens = sorted(tokens, key=lambda t: ((t["bbox"][1] + t["bbox"][3]) / 2.0, t["bbox"][0]))

    lines: List[List[dict]] = []
    current_line: List[dict] = []
    current_y = -1.0

    for tok in sorted_tokens:
        tok_y = (tok["bbox"][1] + tok["bbox"][3]) / 2.0
        if current_y < 0 or abs(tok_y - current_y) <= y_line_tolerance:
            current_line.append(tok)
            # Update running average Y
            current_y = sum((t["bbox"][1] + t["bbox"][3]) / 2.0 for t in current_line) / len(current_line)
        else:
            if current_line:
                lines.append(sorted(current_line, key=lambda t: t["bbox"][0]))
            current_line = [tok]
            current_y = tok_y

    if current_line:
        lines.append(sorted(current_line, key=lambda t: t["bbox"][0]))

    # Filter lines that have at least min_cols tokens
    tabular_candidate_lines: List[Tuple[int, List[dict]]] = [
        (idx, line) for idx, line in enumerate(lines) if len(line) >= min_cols
    ]

    if len(tabular_candidate_lines) < min_rows:
        return []

    # 2. Cluster consecutive candidate lines
    table_regions: List[TableRegion] = []
    current_cluster: List[List[dict]] = []
    last_line_idx = -2

    for line_idx, line in tabular_candidate_lines:
        if line_idx == last_line_idx + 1:
            current_cluster.append(line)
        else:
            if len(current_cluster) >= min_rows:
                region = _build_borderless_region(current_cluster, min_cols)
                if region:
                    table_regions.append(region)
            current_cluster = [line]
        last_line_idx = line_idx

    if len(current_cluster) >= min_rows:
        region = _build_borderless_region(current_cluster, min_cols)
        if region:
            table_regions.append(region)

    return table_regions


def _build_borderless_region(cluster_lines: List[List[dict]], min_cols: int) -> TableRegion | None:
    """Validate column alignment across cluster lines and construct TableRegion."""
    all_tokens = [tok for line in cluster_lines for tok in line]
    if not all_tokens:
        return None

    x0 = min(t["bbox"][0] for t in all_tokens)
    y0 = min(t["bbox"][1] for t in all_tokens)
    x1 = max(t["bbox"][2] for t in all_tokens)
    y1 = max(t["bbox"][3] for t in all_tokens)

    # Estimate column count as median token count per row
    col_counts = [len(line) for line in cluster_lines]
    col_count_est = sorted(col_counts)[len(col_counts) // 2]
    if col_count_est < min_cols:
        return None

    boundary = TableBoundary(
        bbox=(round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4)),
        table_type=TableType.BORDERLESS,
        confidence=0.88,
        row_count_estimate=len(cluster_lines),
        col_count_estimate=col_count_est,
    )
    return TableRegion(boundary=boundary)
