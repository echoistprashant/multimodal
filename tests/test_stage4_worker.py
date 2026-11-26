"""Integration tests for Phase 9 Part 9.4: JSON Repair, Multi-Page Stitching, and Stage 4 Worker."""

import asyncio
from app.extraction.repair import repair_and_parse_json
from app.extraction.stitcher import MultiPageItemStitcher
from app.pipeline.stage4_extraction_worker import Stage4ExtractionWorker
from app.routing.schema import RouteType
from app.schemas.invoice import InvoiceSchema


def test_repair_and_parse_json() -> None:
    """Verify resilient repair of markdown-fenced, single-quoted, and trailing-comma JSON."""
    # 1. Markdown code fence wrapping
    fenced_raw = "Here is the extracted invoice:\n```json\n{\n  \"invoice_number\": \"INV-990\",\n  \"total_amount\": 450.00\n}\n```\nHope this helps!"
    parsed_1 = repair_and_parse_json(fenced_raw)
    assert parsed_1["invoice_number"] == "INV-990"
    assert parsed_1["total_amount"] == 450.00

    # 2. Trailing comma before closing brace
    trailing_comma_raw = '{\n  "invoice_number": "INV-881",\n  "total_amount": 120.00,\n}'
    parsed_2 = repair_and_parse_json(trailing_comma_raw)
    assert parsed_2["invoice_number"] == "INV-881"

    # 3. Single quotes around keys
    single_quote_raw = "{'invoice_number': 'INV-771', 'total_amount': 85.0}"
    parsed_3 = repair_and_parse_json(single_quote_raw)
    assert parsed_3["invoice_number"] == "INV-771"


def test_multipage_item_stitcher() -> None:
    """Verify stitcher consolidates line items across pages and retains summary totals."""
    stitcher = MultiPageItemStitcher()

    page_1 = {
        "invoice_number": "INV-GLOBAL-104",
        "vendor": {"name": "Industrial Supplies Corp"},
        "line_items": [
            {"description": "Heavy Duty Steel Bolts", "quantity": 100.0, "amount": 250.0},
            {"description": "Industrial Lubricant 5L", "quantity": 10.0, "amount": 150.0},
        ],
    }

    page_2 = {
        "invoice_number": "INV-GLOBAL-104",
        "line_items": [
            {"description": "Industrial Lubricant 5L", "quantity": 10.0, "amount": 150.0},  # Duplicate running header
            {"description": "Safety Helmet Grade A", "quantity": 5.0, "amount": 125.0},
        ],
        "subtotal": 525.0,
        "tax_amount": 50.0,
        "total_amount": 575.0,
    }

    stitched = stitcher.stitch_pages([page_1, page_2], target_schema_cls=InvoiceSchema)
    assert stitched["invoice_number"] == "INV-GLOBAL-104"
    assert stitched["vendor"]["name"] == "Industrial Supplies Corp"
    assert stitched["total_amount"] == 575.00
    # Line items should be deduped to 3 items
    assert len(stitched["line_items"]) == 3
    descriptions = [item["description"] for item in stitched["line_items"]]
    assert "Heavy Duty Steel Bolts" in descriptions
    assert "Industrial Lubricant 5L" in descriptions
    assert "Safety Helmet Grade A" in descriptions


def test_stage4_worker_end_to_end() -> None:
    """Verify Stage 4 worker executes classification, multi-page extraction, and stitching."""
    async def _run() -> None:
        worker = Stage4ExtractionWorker()

        pages_content = [
            {
                "page_number": 1,
                "markdown_content": (
                    "# TAX INVOICE #INV-CORP-501\n"
                    "Vendor: Enterprise Software Labs\n"
                    "Bill To: FinTech Solutions Inc\n"
                    "| Item | Amount |\n"
                    "| --- | --- |\n"
                    "| Cloud Platform License | $5,000.00 |\n"
                ),
                "route": RouteType.NATIVE,
            },
            {
                "page_number": 2,
                "markdown_content": (
                    "Total Amount Due: $5,000.00\n"
                    "Payment Terms: Net 30\n"
                ),
                "route": RouteType.NATIVE,
            },
        ]

        result = await worker.process_document(
            document_id="doc-test-123",
            pages_content=pages_content,
        )

        assert result.document_id == "doc-test-123"
        assert result.doc_type == "invoice"
        assert result.classification_confidence > 0.60
        assert result.total_pages_processed == 2
        assert "invoice_number" in result.extracted_data

    asyncio.run(_run())
