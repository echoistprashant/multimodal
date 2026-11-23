"""Geometry Package.

Bounding box normalization, spatial overlapping, and IoU evaluation utilities.
"""

from app.geometry.normalization import denormalize_coordinates, normalize_coordinates
from app.geometry.spatial import compute_intersection, compute_iou, union_bounding_boxes

__all__ = [
    "compute_intersection",
    "compute_iou",
    "denormalize_coordinates",
    "normalize_coordinates",
    "union_bounding_boxes",
]
