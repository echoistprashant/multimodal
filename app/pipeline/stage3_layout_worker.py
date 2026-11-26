"""Stage 3 Pipeline Worker: Document Layout Analysis and Table Extraction.

Orchestrates page block segmentation, bordered/borderless table detection,
grid cell reconstruction, and multi-format layout-aware serialization.
"""

from typing import Any, List, Optional
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field

from app.core.logging import get_logger
from app.layout.html_serializer import serialize_blocks_to_html
from app.layout.markdown_serializer import serialize_blocks_to_markdown
from app.layout.schema import LayoutBlock
from app.layout.xy_cut import segment_page_layout
from app.tables.bordered import detect_bordered_tables
from app.tables.borderless import detect_borderless_tables
from app.tables.grid_reconstructor import reconstruct_table_grid
from app.tables.grid_schema import StructuredTable
from app.tables.header_inference import infer_table_headers

logger = get_logger("app.pipeline.stage3_layout_worker")


class Stage3LayoutResult(BaseModel):
    """Encapsulates the complete layout analysis output for a single document page."""

    model_config = ConfigDict(frozen=True)

    page_number: int = Field(ge=1)
    blocks: List[LayoutBlock] = Field(default_factory=list)
    tables: List[StructuredTable] = Field(default_factory=list)
    markdown_content: str = Field(default="")
    html_content: str = Field(default="")


class Stage3LayoutWorker:
    """Worker processing layout analysis and tabular grid extraction."""

    def process_page(
        self,
        page_number: int,
        tokens: List[dict],
        image: Optional[Image.Image] = None,
    ) -> Stage3LayoutResult:
        """Execute Stage 3 layout analysis pipeline on page tokens and optional image."""
        logger.info(f"Executing Stage 3 Layout Worker on page {page_number} with {len(tokens)} tokens.")

        # 1. Detect Tables (Bordered and Borderless)
        detected_regions = []
        if image is not None:
            bordered = detect_bordered_tables(image)
            detected_regions.extend(bordered)

        borderless = detect_borderless_tables(tokens)
        detected_regions.extend(borderless)

        # 2. Reconstruct Structured Tables
        structured_tables: List[StructuredTable] = []
        table_covered_token_ids = set()

        for region in detected_regions:
            t = reconstruct_table_grid(region, tokens)
            if t.num_rows > 0:
                headers = infer_table_headers(t)
                # Re-assign inferred headers
                t_with_headers = StructuredTable(
                    table_id=t.table_id,
                    page_number=page_number,
                    bbox=t.bbox,
                    num_rows=t.num_rows,
                    num_cols=t.num_cols,
                    headers=headers,
                    rows=t.rows,
                )
                structured_tables.append(t_with_headers)

                # Mark tokens inside this table boundary
                bx0, by0, bx1, by1 = region.boundary.bbox
                for tok in tokens:
                    if not (tok["bbox"][2] < bx0 or tok["bbox"][0] > bx1 or tok["bbox"][3] < by0 or tok["bbox"][1] > by1):
                        table_covered_token_ids.add(tok.get("id", str(tok["bbox"])))

        # 3. Filter non-table tokens for paragraph / header block segmentation
        non_table_tokens = [
            t for t in tokens
            if t.get("id", str(t["bbox"])) not in table_covered_token_ids
        ]

        # 4. Perform Recursive XY-Cut on non-table text
        blocks = segment_page_layout(non_table_tokens)

        # 5. Serialize to Markdown and HTML
        md_text = serialize_blocks_to_markdown(blocks, structured_tables)
        html_markup = serialize_blocks_to_html(blocks, structured_tables, include_coordinates=True)

        return Stage3LayoutResult(
            page_number=page_number,
            blocks=blocks,
            tables=structured_tables,
            markdown_content=md_text,
            html_content=html_markup,
        )
