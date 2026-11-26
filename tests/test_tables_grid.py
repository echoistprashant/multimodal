"""Unit tests for Phase 7 Part 7.3: Table Grid Reconstruction and Header Inference."""

from app.tables.grid_reconstructor import reconstruct_table_grid
from app.tables.header_inference import infer_table_headers, normalize_header_text
from app.tables.schema import TableBoundary, TableRegion, TableType


def test_reconstruct_table_grid_matrix() -> None:
    """Verify reconstruct_table_grid correctly assembles 2D cell matrix."""
    region = TableRegion(
        boundary=TableBoundary(
            bbox=(0.10, 0.20, 0.90, 0.50),
            table_type=TableType.BORDERLESS,
            confidence=0.90,
            row_count_estimate=3,
            col_count_estimate=3,
        )
    )

    tokens = [
        # Row 0 (Headers)
        {"text": "Service", "bbox": (0.12, 0.21, 0.30, 0.24)},
        {"text": "Hours", "bbox": (0.45, 0.21, 0.55, 0.24)},
        {"text": "Rate", "bbox": (0.75, 0.21, 0.85, 0.24)},

        # Row 1
        {"text": "Architecture Design", "bbox": (0.12, 0.30, 0.35, 0.33)},
        {"text": "40", "bbox": (0.45, 0.30, 0.50, 0.33)},
        {"text": "$150/hr", "bbox": (0.75, 0.30, 0.85, 0.33)},

        # Row 2
        {"text": "Code Implementation", "bbox": (0.12, 0.40, 0.35, 0.43)},
        {"text": "80", "bbox": (0.45, 0.40, 0.50, 0.43)},
        {"text": "$125/hr", "bbox": (0.75, 0.40, 0.85, 0.43)},
    ]

    table = reconstruct_table_grid(region, tokens)
    assert table.num_rows == 3
    assert table.num_cols == 3
    assert len(table.rows) == 3

    # Check headers
    assert table.rows[0].is_header_row is True
    assert table.rows[0].cells[0].text == "Service"
    assert table.rows[0].cells[1].text == "Hours"
    assert table.rows[0].cells[2].text == "Rate"

    # Check row 1 data
    assert table.rows[1].is_header_row is False
    assert table.rows[1].cells[0].text == "Architecture Design"
    assert table.rows[1].cells[1].text == "40"
    assert table.rows[1].cells[2].text == "$150/hr"


def test_infer_table_headers() -> None:
    """Verify header keyword matching and text cleaning."""
    assert normalize_header_text("## Item Description : ") == "Item Description"
    assert normalize_header_text(" Total   Amount   ") == "Total Amount"

    region = TableRegion(
        boundary=TableBoundary(
            bbox=(0.1, 0.1, 0.9, 0.4),
            table_type=TableType.BORDERLESS,
        )
    )
    tokens = [
        {"text": "Description:", "bbox": (0.15, 0.12, 0.35, 0.15)},
        {"text": "Quantity", "bbox": (0.50, 0.12, 0.65, 0.15)},
        {"text": "Total ($)", "bbox": (0.75, 0.12, 0.88, 0.15)},
    ]
    table = reconstruct_table_grid(region, tokens)
    headers = infer_table_headers(table)
    assert headers == ["Description", "Quantity", "Total ($)"]
