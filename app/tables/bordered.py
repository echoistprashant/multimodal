"""Morphological Line Detector for Bordered Tables.

Extracts explicit horizontal and vertical grid lines from page images using
directional morphological kernels, detects table grid boundaries, and estimates cell counts.
"""

from typing import List, Tuple, Union
import numpy as np
from PIL import Image
from scipy import ndimage

from app.tables.schema import TableBoundary, TableRegion, TableType
from app.triage.visual_edges import _to_grayscale_array


def detect_bordered_tables(
    image: Union[Image.Image, np.ndarray],
    min_line_len_ratio: float = 0.08,
    min_table_area_ratio: float = 0.02,
) -> List[TableRegion]:
    """Detect grid-bordered tables using horizontal and vertical morphological line kernels.

    Args:
        image: Page image as PIL Image or ndarray.
        min_line_len_ratio: Minimum line length as a fraction of image dimension.
        min_table_area_ratio: Minimum bounding area to qualify as a valid table.

    Returns:
        List of detected TableRegion objects with line coordinates and bounding limits.
    """
    gray = _to_grayscale_array(image)
    height, width = gray.shape
    if height == 0 or width == 0:
        return []

    page_area = float(height * width)

    # 1. Binarize: dark lines on light background
    binary = gray < 200.0

    # 2. Extract horizontal lines using elongated horizontal structuring element
    h_kernel_len = max(int(width * min_line_len_ratio), 15)
    h_struct = np.ones((1, h_kernel_len), dtype=bool)
    h_lines_mask = ndimage.binary_opening(binary, structure=h_struct)

    # 3. Extract vertical lines using elongated vertical structuring element
    v_kernel_len = max(int(height * min_line_len_ratio), 15)
    v_struct = np.ones((v_kernel_len, 1), dtype=bool)
    v_lines_mask = ndimage.binary_opening(binary, structure=v_struct)

    # 4. Table grid mask is the dilated intersection/union of horizontal and vertical lines
    combined_mask = h_lines_mask | v_lines_mask
    connect_struct = np.ones((7, 7), dtype=bool)
    table_blobs = ndimage.binary_closing(combined_mask, structure=connect_struct, iterations=2)

    # 5. Segment table regions via connected component labeling
    labeled, num_features = ndimage.label(table_blobs)
    slices = ndimage.find_objects(labeled)

    table_regions: List[TableRegion] = []

    for sl in slices:
        if sl is None:
            continue
        y_slice, x_slice = sl
        h = y_slice.stop - y_slice.start
        w = x_slice.stop - x_slice.start
        area = w * h

        if area < page_area * min_table_area_ratio:
            continue

        # Check line intersections within this region
        sub_h = h_lines_mask[y_slice, x_slice]
        sub_v = v_lines_mask[y_slice, x_slice]

        # Calculate row lines (horizontal line projections)
        h_proj = np.sum(sub_h, axis=1) > (w * 0.40)
        row_count = max(int(np.sum(ndimage.label(h_proj)[1])), 1)

        # Calculate column lines (vertical line projections)
        v_proj = np.sum(sub_v, axis=0) > (h * 0.40)
        col_count = max(int(np.sum(ndimage.label(v_proj)[1])), 1)

        # A valid bordered table has at least 2 horizontal lines or 2 vertical lines
        if row_count >= 2 or col_count >= 2:
            norm_bbox = (
                round(x_slice.start / width, 4),
                round(y_slice.start / height, 4),
                round(x_slice.stop / width, 4),
                round(y_slice.stop / height, 4),
            )
            boundary = TableBoundary(
                bbox=norm_bbox,
                table_type=TableType.BORDERED if (row_count >= 2 and col_count >= 2) else TableType.PARTIAL,
                confidence=0.92,
                row_count_estimate=max(row_count - 1, 1),
                col_count_estimate=max(col_count - 1, 1),
            )
            table_regions.append(TableRegion(boundary=boundary))

    return table_regions
