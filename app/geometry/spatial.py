"""Spatial Overlap, IoU, and Bounding Box Union Algorithms.

Implements geometric operations required for grounding extracted entities
and evaluating bounding box detection accuracy.
"""

from typing import Sequence
from app.parser.schema import BoundingBox


def compute_intersection(box_a: BoundingBox, box_b: BoundingBox) -> float:
    """Calculate intersection area between two normalized bounding boxes."""
    x_left = max(box_a.x0, box_b.x0)
    y_top = max(box_a.y0, box_b.y0)
    x_right = min(box_a.x1, box_b.x1)
    y_bottom = min(box_a.y1, box_b.y1)

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    return (x_right - x_left) * (y_bottom - y_top)


def compute_iou(box_a: BoundingBox, box_b: BoundingBox) -> float:
    """Compute Intersection-over-Union (IoU) metric between two bounding boxes."""
    intersection = compute_intersection(box_a, box_b)
    if intersection <= 0.0:
        return 0.0

    area_a = (box_a.x1 - box_a.x0) * (box_a.y1 - box_a.y0)
    area_b = (box_b.x1 - box_b.x0) * (box_b.y1 - box_b.y0)
    union = area_a + area_b - intersection

    if union <= 0.0:
        return 0.0
    return round(intersection / union, 4)


def union_bounding_boxes(boxes: Sequence[BoundingBox]) -> BoundingBox:
    """Compute the minimal bounding box enclosing all provided bounding boxes."""
    if not boxes:
        raise ValueError("Cannot compute union of empty bounding box collection")

    min_x0 = min(b.x0 for b in boxes)
    min_y0 = min(b.y0 for b in boxes)
    max_x1 = max(b.x1 for b in boxes)
    max_y1 = max(b.y1 for b in boxes)

    return BoundingBox(
        x0=round(min_x0, 4),
        y0=round(min_y0, 4),
        x1=round(max_x1, 4),
        y1=round(max_y1, 4),
    )
