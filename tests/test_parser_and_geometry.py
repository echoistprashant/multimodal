"""Unit tests for Phase 4: Geometry, Normalization, Rotation, and Spatial Operations."""

import pytest
from app.geometry.normalization import denormalize_coordinates, normalize_coordinates
from app.geometry.spatial import compute_intersection, compute_iou, union_bounding_boxes
from app.geometry.transform import rotate_bounding_box
from app.parser.schema import BoundingBox, Token


def test_coordinate_normalization() -> None:
    """Verify conversion between absolute pixel points and fractional [0.0, 1.0] coordinates."""
    page_w, page_h = 1000.0, 2000.0
    bbox = normalize_coordinates(
        x0=100.0,
        y0=200.0,
        x1=500.0,
        y1=800.0,
        page_width=page_w,
        page_height=page_h,
    )
    assert bbox.x0 == 0.1
    assert bbox.y0 == 0.1
    assert bbox.x1 == 0.5
    assert bbox.y1 == 0.4

    # Denormalize
    px0, py0, px1, py1 = denormalize_coordinates(bbox, target_width=1000, target_height=2000)
    assert px0 == 100
    assert py0 == 200
    assert px1 == 500
    assert py1 == 800


def test_invalid_page_dimensions() -> None:
    """Ensure zero or negative page dimensions raise ValueError."""
    with pytest.raises(ValueError, match="Page dimensions must be positive"):
        normalize_coordinates(10, 10, 50, 50, 0, 100)


def test_spatial_iou_and_intersection() -> None:
    """Verify Intersection-over-Union calculation for exact, partial, and disjoint boxes."""
    box_a = BoundingBox(x0=0.0, y0=0.0, x1=0.5, y1=0.5)
    box_b = BoundingBox(x0=0.0, y0=0.0, x1=0.5, y1=0.5)
    # Identical boxes -> IoU = 1.0
    assert compute_iou(box_a, box_b) == 1.0

    # Disjoint boxes -> IoU = 0.0
    box_c = BoundingBox(x0=0.6, y0=0.6, x1=0.9, y1=0.9)
    assert compute_iou(box_a, box_c) == 0.0
    assert compute_intersection(box_a, box_c) == 0.0

    # Partial overlap
    box_d = BoundingBox(x0=0.25, y0=0.0, x1=0.75, y1=0.5)
    iou = compute_iou(box_a, box_d)
    assert 0.0 < iou < 1.0


def test_bounding_box_union() -> None:
    """Verify union of multiple token bounding boxes into single enclosing box."""
    tokens = [
        Token(text="Total", bbox=BoundingBox(x0=0.6, y0=0.8, x1=0.7, y1=0.85)),
        Token(text="Amount:", bbox=BoundingBox(x0=0.71, y0=0.8, x1=0.8, y1=0.85)),
        Token(text="$500.00", bbox=BoundingBox(x0=0.82, y0=0.8, x1=0.95, y1=0.85)),
    ]
    united = union_bounding_boxes([t.bbox for t in tokens])
    assert united.x0 == 0.6
    assert united.y0 == 0.8
    assert united.x1 == 0.95
    assert united.y1 == 0.85


def test_bounding_box_rotation() -> None:
    """Verify 90, 180, and 270 degree spatial transformations."""
    original = BoundingBox(x0=0.1, y0=0.2, x1=0.4, y1=0.5)

    # 0 degrees
    assert rotate_bounding_box(original, 0) == original

    # 90 degrees clockwise: x0=1-y1, y0=x0, x1=1-y0, y1=x1
    rot_90 = rotate_bounding_box(original, 90)
    assert rot_90.x0 == round(1.0 - 0.5, 4)
    assert rot_90.y0 == 0.1
    assert rot_90.x1 == round(1.0 - 0.2, 4)
    assert rot_90.y1 == 0.4

    # 180 degrees
    rot_180 = rotate_bounding_box(original, 180)
    assert rot_180.x0 == round(1.0 - 0.4, 4)
    assert rot_180.y0 == round(1.0 - 0.5, 4)

    # 270 degrees
    rot_270 = rotate_bounding_box(original, 270)
    assert rot_270.x0 == 0.2
    assert rot_270.y1 == round(1.0 - 0.1, 4)
