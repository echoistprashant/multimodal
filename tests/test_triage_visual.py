"""Unit tests for Phase 6 Part 6.2: Visual Complexity and Graphic Region Detection."""

import numpy as np
from PIL import Image, ImageDraw

from app.triage.visual_edges import compute_edge_density
from app.triage.visual_regions import detect_graphics_regions, evaluate_visual_complexity
from app.triage.visual_schema import VisualComplexityScore


def test_blank_page_visual_complexity() -> None:
    """Verify an empty white page produces near-zero edge density and complexity."""
    blank_img = Image.new("RGB", (600, 800), color=(255, 255, 255))
    edge_density, gradient_energy = compute_edge_density(blank_img)
    assert edge_density == 0.0
    assert gradient_energy == 0.0

    score = evaluate_visual_complexity(blank_img)
    assert isinstance(score, VisualComplexityScore)
    assert score.has_complex_graphics is False
    assert len(score.graphics_regions) == 0
    assert score.complexity_score < 0.10
    assert score.recommended_mode == "native"


def test_page_with_diagram_detection() -> None:
    """Verify page with large filled shapes (chart/diagram) triggers graphics detection."""
    img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Draw simulated chart (large dark rectangle and circle)
    draw.rectangle([200, 200, 600, 500], fill=(50, 50, 50), outline=(0, 0, 0))
    draw.ellipse([300, 600, 500, 800], fill=(80, 80, 80), outline=(0, 0, 0))

    regions = detect_graphics_regions(img)
    assert len(regions) >= 1

    # Verify normalized coordinates
    for x0, y0, x1, y1 in regions:
        assert 0.0 <= x0 < x1 <= 1.0
        assert 0.0 <= y0 < y1 <= 1.0

    score = evaluate_visual_complexity(img)
    assert score.has_complex_graphics is True
    assert score.recommended_mode == "vlm"
    assert score.complexity_score > 0.40


def test_numpy_array_input_support() -> None:
    """Verify visual edge functions support ndarray as well as PIL Images."""
    arr = np.full((400, 400), 255, dtype=np.uint8)
    # Add a horizontal stripe
    arr[150:250, 100:300] = 0

    edge_density, grad = compute_edge_density(arr)
    assert edge_density > 0.0
    assert grad > 0.0
