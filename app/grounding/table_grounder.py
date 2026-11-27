"""Table-Cell Coordinate Resolver for Line Item Grounding.

Maps extracted line-item dictionaries back to StructuredTable rows and cell bounding boxes
for precise row-level visual provenance.
"""

from typing import Any, Dict, List, Optional
from app.grounding.bbox_merger import merge_bounding_boxes
from app.grounding.matcher import compute_fuzzy_similarity
from app.grounding.schema import GroundedSpan, GroundingStatus, ProvenanceMatch
from app.tables.grid_schema import StructuredTable


def ground_line_item_in_tables(
    item_index: int,
    item_dict: Dict[str, Any],
    tables: List[StructuredTable],
    min_similarity: float = 0.75,
) -> ProvenanceMatch:
    """Locate an extracted line item within reconstructed StructuredTables."""
    description = str(item_dict.get("description", "")).strip()
    field_path = f"line_items[{item_index}]"

    if not description or not tables:
        return ProvenanceMatch(
            field_path=field_path,
            extracted_value=item_dict,
            status=GroundingStatus.UNGROUNDED,
            grounded=False,
            confidence=0.0,
        )

    best_span: Optional[GroundedSpan] = None
    best_score = 0.0

    for table in tables:
        for row in table.rows:
            if row.is_header_row:
                continue
            row_text = " ".join(c.text for c in row.cells if c.text).strip()
            # Compare against individual cells and full row text
            cell_scores = [compute_fuzzy_similarity(description, c.text) for c in row.cells if c.text]
            max_cell_score = max(cell_scores) if cell_scores else 0.0
            score = max(max_cell_score, compute_fuzzy_similarity(description, row_text))

            if score >= min_similarity and score > best_score:
                best_score = score
                row_bbox = merge_bounding_boxes([c.bbox for c in row.cells])
                best_span = GroundedSpan(
                    page_no=table.page_number,
                    bbox=row_bbox,
                    source_text=row_text,
                    token_ids=[c.cell_id for c in row.cells],
                    match_score=score,
                )

    if best_span:
        status = GroundingStatus.EXACT if best_score == 1.0 else GroundingStatus.FUZZY
        return ProvenanceMatch(
            field_path=field_path,
            extracted_value=item_dict,
            status=status,
            grounded=True,
            confidence=best_score,
            best_span=best_span,
            candidate_spans=[best_span],
        )

    return ProvenanceMatch(
        field_path=field_path,
        extracted_value=item_dict,
        status=GroundingStatus.UNGROUNDED,
        grounded=False,
        confidence=0.0,
    )
