"""Recursive XY-Cut Page Segmentation and Reading Order Algorithm.

Decomposes complex document layouts (multi-column, sidebars, mixed text) into
hierarchical blocks and reconstructs natural human reading order.
"""

from typing import List, Tuple
from app.layout.projection import compute_projection_profile, find_projection_valleys
from app.layout.schema import LayoutBlock, SemanticBlockType


def _bounding_box_union(boxes: List[Tuple[float, float, float, float]]) -> Tuple[float, float, float, float]:
    """Calculate the minimal enclosing bounding box covering all given boxes."""
    if not boxes:
        return (0.0, 0.0, 0.0, 0.0)
    x0 = min(b[0] for b in boxes)
    y0 = min(b[1] for b in boxes)
    x1 = max(b[2] for b in boxes)
    y1 = max(b[3] for b in boxes)
    return (round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4))


def _recursive_xy_cut(
    items: List[dict],
    min_horizontal_gap: float = 0.015,
    min_vertical_gap: float = 0.025,
) -> List[List[dict]]:
    """Recursively partition items using alternating horizontal and vertical projection cuts."""
    if len(items) <= 1:
        return [items]

    bboxes = [it["bbox"] for it in items]
    num_bins = 1000

    # 1. Attempt Horizontal Cut (splitting vertical paragraphs/sections)
    h_profile = compute_projection_profile(bboxes, axis="horizontal", num_bins=num_bins)
    min_h_bins = int(min_horizontal_gap * num_bins)
    # Exclude margins (valleys at the very beginning or very end)
    h_valleys = [v for v in find_projection_valleys(h_profile, min_valley_width=min_h_bins)
                 if v[0] > 10 and v[1] < num_bins - 10]

    if h_valleys:
        # Choose the widest valley to cut
        best_valley = max(h_valleys, key=lambda v: v[1] - v[0])
        cut_y = (best_valley[0] + best_valley[1]) / (2.0 * num_bins)

        top_items = [it for it in items if (it["bbox"][1] + it["bbox"][3]) / 2.0 <= cut_y]
        bottom_items = [it for it in items if (it["bbox"][1] + it["bbox"][3]) / 2.0 > cut_y]

        if top_items and bottom_items:
            return (
                _recursive_xy_cut(top_items, min_horizontal_gap, min_vertical_gap)
                + _recursive_xy_cut(bottom_items, min_horizontal_gap, min_vertical_gap)
            )

    # 2. Attempt Vertical Cut (splitting side-by-side columns)
    v_profile = compute_projection_profile(bboxes, axis="vertical", num_bins=num_bins)
    min_v_bins = int(min_vertical_gap * num_bins)
    v_valleys = [v for v in find_projection_valleys(v_profile, min_valley_width=min_v_bins)
                 if v[0] > 10 and v[1] < num_bins - 10]

    if v_valleys:
        best_valley = max(v_valleys, key=lambda v: v[1] - v[0])
        cut_x = (best_valley[0] + best_valley[1]) / (2.0 * num_bins)

        left_items = [it for it in items if (it["bbox"][0] + it["bbox"][2]) / 2.0 <= cut_x]
        right_items = [it for it in items if (it["bbox"][0] + it["bbox"][2]) / 2.0 > cut_x]

        if left_items and right_items:
            return (
                _recursive_xy_cut(left_items, min_horizontal_gap, min_vertical_gap)
                + _recursive_xy_cut(right_items, min_horizontal_gap, min_vertical_gap)
            )

    # Cannot partition further - return as single leaf cluster
    return [items]


def segment_page_layout(
    tokens: List[dict],
    min_horizontal_gap: float = 0.015,
    min_vertical_gap: float = 0.025,
) -> List[LayoutBlock]:
    """Segment page tokens into hierarchical LayoutBlocks ordered by natural reading sequence.

    Args:
        tokens: List of dicts, each with 'bbox' [x0, y0, x1, y1] and 'text'.
        min_horizontal_gap: Minimum vertical gap threshold for horizontal cuts.
        min_vertical_gap: Minimum horizontal gap threshold for vertical column cuts.

    Returns:
        List of LayoutBlock instances with sequential reading_order.
    """
    if not tokens:
        return []

    clusters = _recursive_xy_cut(
        tokens,
        min_horizontal_gap=min_horizontal_gap,
        min_vertical_gap=min_vertical_gap,
    )

    blocks: List[LayoutBlock] = []
    for order_idx, cluster in enumerate(clusters):
        boxes = [item["bbox"] for item in cluster]
        union_bbox = _bounding_box_union(boxes)

        # Sort tokens inside cluster top-to-bottom, left-to-right
        sorted_cluster = sorted(cluster, key=lambda it: (it["bbox"][1], it["bbox"][0]))
        cluster_text = " ".join(it.get("text", "").strip() for it in sorted_cluster if it.get("text"))

        # Infer simple block semantic type based on length and position
        block_type = SemanticBlockType.PARAGRAPH
        if order_idx == 0 and len(cluster_text) < 120 and union_bbox[1] < 0.20:
            block_type = SemanticBlockType.HEADER
        elif union_bbox[3] > 0.92 and len(cluster_text) < 100:
            block_type = SemanticBlockType.FOOTER

        blocks.append(
            LayoutBlock(
                type=block_type,
                bbox=union_bbox,
                reading_order=order_idx,
                text=cluster_text,
                children_ids=[str(it.get("id", i)) for i, it in enumerate(sorted_cluster)],
            )
        )

    return blocks
