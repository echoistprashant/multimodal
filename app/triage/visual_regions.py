"""Non-Text Graphical Region Detector and Visual Complexity Evaluator.

Detects diagrams, charts, signatures, and photographic elements by analyzing
morphological contours, bounding aspect ratios, and spatial area occupancy.
"""

from typing import Union
import cv2
import numpy as np
from PIL import Image

from app.triage.visual_edges import _to_grayscale_array, compute_edge_density
from app.triage.visual_schema import VisualComplexityScore


def detect_graphics_regions(
    image: Union[Image.Image, np.ndarray],
    min_area_fraction: float = 0.02,
    max_text_aspect_ratio: float = 6.0,
) -> list[tuple[float, float, float, float]]:
    """Detect bounding boxes of large non-text graphical regions (charts, diagrams, stamps).

    Args:
        image: Page image as PIL or ndarray.
        min_area_fraction: Minimum area fraction of the page to qualify as a graphic element.
        max_text_aspect_ratio: Max aspect ratio distinguishing graphics from horizontal text lines.

    Returns:
        List of normalized bounding boxes [x0, y0, x1, y1] with values in [0.0, 1.0].
    """
    gray = _to_grayscale_array(image)
    height, width = gray.shape
    if height == 0 or width == 0:
        return []

    page_area = float(height * width)

    # Otsu thresholding followed by morphological closing to merge nearby graphical strokes
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Find external contours
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    graphics_boxes: list[tuple[float, float, float, float]] = []
    min_area = page_area * min_area_fraction

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        if area < min_area:
            continue

        aspect_ratio = max(w / max(h, 1), h / max(w, 1))
        # Text blocks often have high aspect ratios (> 6.0) or low pixel density
        if aspect_ratio > max_text_aspect_ratio:
            continue

        # Check foreground fill density inside the contour bounding box
        roi = binary[y : y + h, x : x + w]
        fill_ratio = cv2.countNonZero(roi) / max(area, 1)

        # Dense illustrations, charts, diagrams typically have fill ratio between 0.15 and 0.90
        if 0.10 <= fill_ratio <= 0.95:
            norm_box = (
                round(x / width, 4),
                round(y / height, 4),
                round((x + w) / width, 4),
                round((y + h) / height, 4),
            )
            graphics_boxes.append(norm_box)

    return graphics_boxes


def evaluate_visual_complexity(
    image: Union[Image.Image, np.ndarray],
) -> VisualComplexityScore:
    """Evaluate overall visual complexity and produce routing recommendation."""
    edge_density, gradient_energy = compute_edge_density(image)
    graphics_boxes = detect_graphics_regions(image)

    has_complex_graphics = len(graphics_boxes) > 0

    # Calculate total graphics area coverage
    graphics_area_coverage = 0.0
    for x0, y0, x1, y1 in graphics_boxes:
        graphics_area_coverage += (x1 - x0) * (y1 - y0)
    graphics_area_coverage = min(graphics_area_coverage, 1.0)

    # Composite complexity score [0.0, 1.0]
    # Edge density capped around 0.25 (dense documents), gradient energy scaled
    edge_term = min(edge_density / 0.25, 1.0)
    energy_term = min(gradient_energy / 50.0, 1.0)
    graphics_term = min(graphics_area_coverage / 0.20, 1.0)

    complexity_score = round(
        0.4 * edge_term + 0.3 * energy_term + 0.3 * graphics_term,
        4,
    )

    # Routing recommendation logic
    if has_complex_graphics or complexity_score >= 0.70:
        recommended_mode = "vlm"
    elif edge_density >= 0.03 or complexity_score >= 0.25:
        recommended_mode = "ocr"
    else:
        recommended_mode = "native"

    return VisualComplexityScore(
        edge_density=edge_density,
        gradient_energy=gradient_energy,
        has_complex_graphics=has_complex_graphics,
        graphics_regions=graphics_boxes,
        complexity_score=complexity_score,
        recommended_mode=recommended_mode,
    )
