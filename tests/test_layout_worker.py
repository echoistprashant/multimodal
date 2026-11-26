"""Integration tests for Phase 7 Part 7.4: Stage 3 Layout and Table Worker."""

from app.layout.html_serializer import serialize_blocks_to_html
from app.layout.markdown_serializer import serialize_blocks_to_markdown
from app.layout.schema import LayoutBlock, SemanticBlockType
from app.pipeline.stage3_layout_worker import Stage3LayoutWorker


def test_stage3_layout_worker_end_to_end() -> None:
    """Verify Stage 3 worker orchestrates segmentation, table extraction, and serialization."""
    tokens = [
        # Top Header
        {"id": "h_1", "text": "INVOICE AND BILLING STATEMENT", "bbox": (0.10, 0.05, 0.90, 0.10)},

        # Intro text
        {"id": "p_1", "text": "Thank you for your business. Please review charges below.", "bbox": (0.10, 0.15, 0.85, 0.18)},

        # Borderless Table (3 rows x 2 cols)
        {"id": "t_r0_c0", "text": "Service Item", "bbox": (0.10, 0.25, 0.45, 0.28)},
        {"id": "t_r0_c1", "text": "Cost ($)", "bbox": (0.65, 0.25, 0.85, 0.28)},

        {"id": "t_r1_c0", "text": "Cloud Database Hosting", "bbox": (0.10, 0.32, 0.45, 0.35)},
        {"id": "t_r1_c1", "text": "250.00", "bbox": (0.65, 0.32, 0.85, 0.35)},

        {"id": "t_r2_c0", "text": "Support Tier Gold", "bbox": (0.10, 0.39, 0.45, 0.42)},
        {"id": "t_r2_c1", "text": "100.00", "bbox": (0.65, 0.39, 0.85, 0.42)},

        # Footer
        {"id": "f_1", "text": "Payment due within 30 days of invoice date.", "bbox": (0.10, 0.93, 0.90, 0.96)},
    ]

    worker = Stage3LayoutWorker()
    result = worker.process_page(page_number=1, tokens=tokens)

    assert result.page_number == 1
    assert len(result.tables) == 1
    table = result.tables[0]
    assert table.num_rows == 3
    assert table.num_cols == 2
    assert "Service Item" in table.headers
    assert "Cost ($)" in table.headers

    # Verify Markdown
    assert "# INVOICE AND BILLING STATEMENT" in result.markdown_content
    assert "| Service Item | Cost ($) |" in result.markdown_content
    assert "| Cloud Database Hosting | 250.00 |" in result.markdown_content
    assert "Payment due within 30 days" in result.markdown_content

    # Verify HTML
    assert "<h1" in result.html_content
    assert "<table data-bbox=" in result.html_content
    assert ">Cloud Database Hosting</td>" in result.html_content
    assert "<footer" in result.html_content


def test_serialization_primitives() -> None:
    """Verify individual markdown and html serialization helpers."""
    blocks = [
        LayoutBlock(
            type=SemanticBlockType.HEADER,
            bbox=(0.1, 0.1, 0.9, 0.15),
            reading_order=0,
            text="Document Title",
        ),
        LayoutBlock(
            type=SemanticBlockType.LIST_ITEM,
            bbox=(0.1, 0.2, 0.9, 0.25),
            reading_order=1,
            text="First action item",
        ),
    ]

    md = serialize_blocks_to_markdown(blocks)
    assert "# Document Title" in md
    assert "- First action item" in md

    html_code = serialize_blocks_to_html(blocks, include_coordinates=False)
    assert "<h1>Document Title</h1>" in html_code
    assert "<ul><li>First action item</li></ul>" in html_code
