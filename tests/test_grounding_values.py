"""Unit tests for Phase 10 Part 10.2: Numeric, Date, and Line-Item Grounding."""

from app.grounding.date_matcher import find_date_spans, parse_date_string
from app.grounding.numeric_matcher import find_numeric_spans, parse_numeric_token
from app.grounding.schema import GroundingStatus
from app.grounding.table_grounder import ground_line_item_in_tables
from app.tables.grid_schema import StructuredTable, TableCell, TableRow


def test_numeric_currency_grounding() -> None:
    """Verify numeric matcher equates formatted currency tokens with float values."""
    assert parse_numeric_token("$1,250.50") == 1250.50
    tokens = [
        {"id": "n1", "text": "Subtotal:", "bbox": (0.1, 0.5, 0.2, 0.53)},
        {"id": "n2", "text": "$1,250.00", "bbox": (0.7, 0.5, 0.85, 0.53)},
    ]
    spans = find_numeric_spans(1250.0, tokens, page_no=1)
    assert len(spans) == 1
    assert spans[0].source_text == "$1,250.00"
    assert spans[0].bbox == (0.7, 0.5, 0.85, 0.53)


def test_date_format_grounding() -> None:
    """Verify date matcher links multi-token calendar strings to ISO-8601 dates."""
    assert parse_date_string("Nov 20, 2026") == "2026-11-20"
    assert parse_date_string("20/11/2026") == "2026-11-20"

    tokens = [
        {"id": "d1", "text": "Date:", "bbox": (0.1, 0.1, 0.2, 0.13)},
        {"id": "d2", "text": "Nov", "bbox": (0.22, 0.1, 0.27, 0.13)},
        {"id": "d3", "text": "20,", "bbox": (0.28, 0.1, 0.32, 0.13)},
        {"id": "d4", "text": "2026", "bbox": (0.33, 0.1, 0.40, 0.13)},
    ]
    spans = find_date_spans("2026-11-20", tokens, page_no=2)
    assert len(spans) == 1
    assert spans[0].page_no == 2
    assert spans[0].bbox == (0.22, 0.1, 0.40, 0.13)


def test_table_line_item_grounding() -> None:
    """Verify line items map back to structured table row bounding boxes."""
    table = StructuredTable(
        page_number=1,
        bbox=(0.1, 0.3, 0.9, 0.5),
        num_rows=2,
        num_cols=2,
        headers=["Description", "Amount"],
        rows=[
            TableRow(row_idx=0, is_header_row=True, cells=[
                TableCell(row_idx=0, col_idx=0, text="Description", bbox=(0.1, 0.3, 0.5, 0.35), is_header=True),
                TableCell(row_idx=0, col_idx=1, text="Amount", bbox=(0.7, 0.3, 0.9, 0.35), is_header=True),
            ]),
            TableRow(row_idx=1, is_header_row=False, cells=[
                TableCell(row_idx=1, col_idx=0, text="GPU Cluster Hosting", bbox=(0.1, 0.36, 0.5, 0.42)),
                TableCell(row_idx=1, col_idx=1, text="$500.00", bbox=(0.7, 0.36, 0.9, 0.42)),
            ]),
        ],
    )

    match = ground_line_item_in_tables(0, {"description": "GPU Cluster Hosting", "amount": 500.0}, [table])
    assert match.grounded is True
    assert match.status == GroundingStatus.EXACT
    assert match.best_span is not None
    assert match.best_span.bbox == (0.1, 0.36, 0.9, 0.42)
