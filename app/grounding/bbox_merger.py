"""Spatial Bounding-Box Union and Coordinate Validator.

Merges multi-token bounding boxes into minimal enclosing rectangles
and enforces normalized [0.0, 1.0] bounds.
"""

from typing import Sequence, Tuple


def clamp_coordinate(val: float) -> float:
    """Clamp a normalized coordinate strictly within [0.0, 1.0]."""
    return round(max(0.0, min(1.0, float(val))), 4)


def merge_bounding_boxes(
    boxes: Sequence[Tuple[float, float, float, float]],
) -> Tuple[float, float, float, float]:
    """Compute the minimal enclosing bounding box for a sequence of [x0, y0, x1, y1] boxes."""
    if not boxes:
        return (0.0, 0.0, 0.0, 0.0)

    x0 = min(b[0] for b in boxes)
    y0 = min(b[1] for b in boxes)
    x1 = max(b[2] for b in boxes)
    y1 = max(b[3] for b in boxes)

    return (
        clamp_coordinate(x0),
        clamp_coordinate(y0),
        clamp_coordinate(x1),
        clamp_coordinate(y1),
    )


def is_valid_normalized_bbox(bbox: Tuple[float, float, float, float]) -> bool:
    """Verify bounding box has valid ordering and lies within [0.0, 1.0]."""
    if len(bbox) != 4:
        return False
    x0, y0, x1, y1 = bbox
    return 0.0 <= x0 <= x1 <= 1.0 and 0.0 <= y0 <= y1 <= 1.0
