"""Unit tests for Phase 7 Part 7.1: Projection Profiling and XY-Cut Layout Segmentation."""

from app.layout.projection import compute_projection_profile, find_projection_valleys
from app.layout.schema import SemanticBlockType
from app.layout.xy_cut import segment_page_layout


def test_projection_profiling() -> None:
    """Verify projection histograms identify whitespace valleys correctly."""
    # Two separated horizontal stripes
    boxes = [
        (0.1, 0.1, 0.9, 0.25),
        (0.1, 0.6, 0.9, 0.75),
    ]
    h_profile = compute_projection_profile(boxes, axis="horizontal", num_bins=100)
    assert h_profile[15] == 1
    assert h_profile[40] == 0  # Mid gap
    assert h_profile[65] == 1

    valleys = find_projection_valleys(h_profile, min_valley_width=10)
    assert len(valleys) >= 1


def test_single_column_paragraph_order() -> None:
    """Verify simple top-to-bottom single column layout preserves sequential reading order."""
    tokens = [
        {"id": "h1", "text": "Annual Financial Report", "bbox": (0.1, 0.05, 0.9, 0.12)},
        {"id": "p1_1", "text": "In fiscal year 2026,", "bbox": (0.1, 0.20, 0.45, 0.25)},
        {"id": "p1_2", "text": "revenue reached records.", "bbox": (0.5, 0.20, 0.9, 0.25)},
        {"id": "p2_1", "text": "Operating margin improved.", "bbox": (0.1, 0.35, 0.9, 0.40)},
    ]

    blocks = segment_page_layout(tokens, min_horizontal_gap=0.03)
    assert len(blocks) == 3
    assert blocks[0].reading_order == 0
    assert blocks[0].type == SemanticBlockType.HEADER
    assert "Annual Financial Report" in blocks[0].text

    assert blocks[1].reading_order == 1
    assert "In fiscal year 2026, revenue reached records." in blocks[1].text

    assert blocks[2].reading_order == 2
    assert "Operating margin improved." in blocks[2].text


def test_two_column_newspaper_reading_order() -> None:
    """Verify XY-Cut reads top header, then left column top-to-bottom, then right column."""
    tokens = [
        # Top banner header
        {"id": "title", "text": "GLOBAL QUARTERLY NEWS", "bbox": (0.1, 0.05, 0.9, 0.12)},

        # Left Column (x: 0.05 to 0.45)
        {"id": "left_top", "text": "Left Col Header.", "bbox": (0.05, 0.25, 0.45, 0.30)},
        {"id": "left_bot", "text": "Left Col Story continues.", "bbox": (0.05, 0.40, 0.45, 0.45)},

        # Right Column (x: 0.55 to 0.95)
        {"id": "right_top", "text": "Right Col Tech Analysis.", "bbox": (0.55, 0.25, 0.95, 0.30)},
        {"id": "right_bot", "text": "Right Col Conclusion.", "bbox": (0.55, 0.40, 0.95, 0.45)},
    ]

    blocks = segment_page_layout(tokens, min_horizontal_gap=0.05, min_vertical_gap=0.05)
    # Header should be first
    assert blocks[0].text == "GLOBAL QUARTERLY NEWS"

    # All left column blocks should precede right column blocks
    block_texts = [b.text for b in blocks]
    assert "Left Col Header." in block_texts[1]
    assert "Left Col Story continues." in block_texts[2]
    assert "Right Col Tech Analysis." in block_texts[3]
    assert "Right Col Conclusion." in block_texts[4]
