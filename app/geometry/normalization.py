"""Spatial Coordinate Normalization and Denormalization Utilities.

Translates between absolute pixel/point dimensions and universal fractional
bounding boxes [0.0, 1.0] for resolution-independent visual rendering.
"""

from app.parser.schema import BoundingBox


def normalize_coordinates(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    page_width: float,
    page_height: float,
) -> BoundingBox:
    """Normalize pixel or point coordinates into fractional [0.0, 1.0] range."""
    if page_width <= 0 or page_height <= 0:
        raise ValueError(f"Page dimensions must be positive, got width={page_width}, height={page_height}")

    norm_x0 = max(0.0, min(1.0, x0 / page_width))
    norm_y0 = max(0.0, min(1.0, y0 / page_height))
    norm_x1 = max(norm_x0, min(1.0, x1 / page_width))
    norm_y1 = max(norm_y0, min(1.0, y1 / page_height))

    return BoundingBox(
        x0=round(norm_x0, 4),
        y0=round(norm_y0, 4),
        x1=round(norm_x1, 4),
        y1=round(norm_y1, 4),
    )


def denormalize_coordinates(
    bbox: BoundingBox,
    target_width: int,
    target_height: int,
) -> tuple[int, int, int, int]:
    """Convert normalized [0.0, 1.0] bounding box to integer pixel coordinates."""
    px0 = int(round(bbox.x0 * target_width))
    py0 = int(round(bbox.y0 * target_height))
    px1 = int(round(bbox.x1 * target_width))
    py1 = int(round(bbox.y1 * target_height))

    return px0, py0, max(px0 + 1, px1), max(py0 + 1, py1)
