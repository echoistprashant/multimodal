"""Coordinate Transformation and Matrix Operations for Rotated Pages.

Maps bounding boxes across orientation changes (0, 90, 180, 270 degrees)
ensuring that bounding box coordinates remain normalized and valid.
"""

from app.parser.schema import BoundingBox


def rotate_bounding_box(bbox: BoundingBox, degrees: int) -> BoundingBox:
    """Transform normalized [0, 1] bounding box by rotation angle in degrees."""
    normalized_angle = degrees % 360

    if normalized_angle == 0:
        return bbox

    if normalized_angle == 90:
        # 90 degrees clockwise
        return BoundingBox(
            x0=round(1.0 - bbox.y1, 4),
            y0=round(bbox.x0, 4),
            x1=round(1.0 - bbox.y0, 4),
            y1=round(bbox.x1, 4),
        )

    if normalized_angle == 180:
        # 180 degrees
        return BoundingBox(
            x0=round(1.0 - bbox.x1, 4),
            y0=round(1.0 - bbox.y1, 4),
            x1=round(1.0 - bbox.x0, 4),
            y1=round(1.0 - bbox.y0, 4),
        )

    if normalized_angle == 270:
        # 270 degrees clockwise (90 counter-clockwise)
        return BoundingBox(
            x0=round(bbox.y0, 4),
            y0=round(1.0 - bbox.x1, 4),
            x1=round(bbox.y1, 4),
            y1=round(1.0 - bbox.x0, 4),
        )

    raise ValueError(f"Unsupported rotation angle: {degrees}. Must be a multiple of 90 degrees.")
