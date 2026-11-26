"""Unit tests for Phase 7 Part 7.2: Bordered and Borderless Table Detection."""

from PIL import Image, ImageDraw

from app.tables.bordered import detect_bordered_tables
from app.tables.borderless import detect_borderless_tables
from app.tables.schema import TableType


def test_bordered_table_detection() -> None:
    """Verify morphological line detector recognizes explicit grid lines."""
    img = Image.new("RGB", (600, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Draw a 3x3 table grid (4 horizontal lines, 4 vertical lines)
    # y lines: 200, 260, 320, 380
    for y in [200, 260, 320, 380]:
        draw.line([(100, y), (500, y)], fill=(0, 0, 0), width=2)

    # x lines: 100, 230, 360, 500
    for x in [100, 230, 360, 500]:
        draw.line([(x, 200), (x, 380)], fill=(0, 0, 0), width=2)

    tables = detect_bordered_tables(img)
    assert len(tables) >= 1
    t = tables[0]
    assert t.boundary.table_type in [TableType.BORDERED, TableType.PARTIAL]
    assert t.boundary.row_count_estimate >= 2
    assert t.boundary.col_count_estimate >= 2
    assert t.boundary.bbox[0] <= 0.20
    assert t.boundary.bbox[2] >= 0.80


def test_borderless_table_detection() -> None:
    """Verify whitespace alignment detects tabular data without borders."""
    tokens = [
        # Row 1 (Headers)
        {"text": "Description", "bbox": (0.10, 0.20, 0.35, 0.23)},
        {"text": "Quantity", "bbox": (0.45, 0.20, 0.55, 0.23)},
        {"text": "Total Price", "bbox": (0.70, 0.20, 0.90, 0.23)},

        # Row 2 (Item 1)
        {"text": "Cloud Server VM", "bbox": (0.10, 0.26, 0.35, 0.29)},
        {"text": "2", "bbox": (0.45, 0.26, 0.50, 0.29)},
        {"text": "$120.00", "bbox": (0.70, 0.26, 0.85, 0.29)},

        # Row 3 (Item 2)
        {"text": "Block Storage SSD", "bbox": (0.10, 0.32, 0.35, 0.35)},
        {"text": "5", "bbox": (0.45, 0.32, 0.50, 0.35)},
        {"text": "$75.00", "bbox": (0.70, 0.32, 0.82, 0.35)},

        # Row 4 (Item 3)
        {"text": "Bandwidth Transfer", "bbox": (0.10, 0.38, 0.35, 0.41)},
        {"text": "1", "bbox": (0.45, 0.38, 0.48, 0.41)},
        {"text": "$15.00", "bbox": (0.70, 0.38, 0.80, 0.41)},
    ]

    tables = detect_borderless_tables(tokens, min_rows=3, min_cols=2)
    assert len(tables) == 1
    t = tables[0]
    assert t.boundary.table_type == TableType.BORDERLESS
    assert t.boundary.row_count_estimate == 4
    assert t.boundary.col_count_estimate == 3


def test_scattered_tokens_negative() -> None:
    """Verify normal unstructured text tokens do not form a table."""
    tokens = [
        {"text": "Header", "bbox": (0.10, 0.10, 0.50, 0.15)},
        {"text": "Single paragraph text spanning the width", "bbox": (0.10, 0.25, 0.90, 0.30)},
        {"text": "Another paragraph below", "bbox": (0.10, 0.40, 0.85, 0.45)},
    ]
    tables = detect_borderless_tables(tokens, min_rows=3, min_cols=2)
    assert len(tables) == 0
