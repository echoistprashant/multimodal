"""Horizontal and Vertical Projection Profiler for Document Segmentation.

Computes spatial projection profiles of bounding boxes across horizontal (Y-axis)
and vertical (X-axis) dimensions to detect column gutters, line breaks, and paragraph boundaries.
"""

from typing import Sequence, Tuple
import numpy as np


def compute_projection_profile(
    bboxes: Sequence[Tuple[float, float, float, float]],
    axis: str = "horizontal",
    num_bins: int = 1000,
) -> np.ndarray:
    """Compute 1D histogram of spatial occupancy across the requested dimension.

    Args:
        bboxes: Sequence of normalized [x0, y0, x1, y1] coordinates in [0.0, 1.0].
        axis: 'horizontal' (projects along Y to find row gaps) or 'vertical' (projects along X to find column gutters).
        num_bins: Resolution of the projection discretization grid.

    Returns:
        1D numpy array of shape (num_bins,) representing occupancy density.
    """
    profile = np.zeros(num_bins, dtype=np.int32)
    if not bboxes:
        return profile

    for x0, y0, x1, y1 in bboxes:
        if axis == "horizontal":
            # Project onto Y-axis (rows)
            start_bin = int(max(0.0, min(1.0, y0)) * (num_bins - 1))
            end_bin = int(max(0.0, min(1.0, y1)) * (num_bins - 1))
        elif axis == "vertical":
            # Project onto X-axis (columns)
            start_bin = int(max(0.0, min(1.0, x0)) * (num_bins - 1))
            end_bin = int(max(0.0, min(1.0, x1)) * (num_bins - 1))
        else:
            raise ValueError(f"Unsupported axis '{axis}'. Must be 'horizontal' or 'vertical'.")

        if start_bin > end_bin:
            start_bin, end_bin = end_bin, start_bin

        profile[start_bin : end_bin + 1] += 1

    return profile


def find_projection_valleys(
    profile: np.ndarray,
    min_valley_width: int = 3,
    occupancy_threshold: int = 0,
) -> list[tuple[int, int]]:
    """Detect contiguous whitespace gaps (valleys) where occupancy <= occupancy_threshold.

    Args:
        profile: 1D projection histogram.
        min_valley_width: Minimum number of consecutive empty bins to qualify as a cut candidate.
        occupancy_threshold: Max occupancy count treated as empty space.

    Returns:
        List of (start_bin, end_bin) tuples marking cuttable whitespace valleys.
    """
    valleys: list[tuple[int, int]] = []
    in_valley = False
    valley_start = 0

    for i, val in enumerate(profile):
        if val <= occupancy_threshold:
            if not in_valley:
                in_valley = True
                valley_start = i
        else:
            if in_valley:
                in_valley = False
                if (i - valley_start) >= min_valley_width:
                    valleys.append((valley_start, i - 1))

    # Check terminal valley
    if in_valley and (len(profile) - valley_start) >= min_valley_width:
        valleys.append((valley_start, len(profile) - 1))

    return valleys
