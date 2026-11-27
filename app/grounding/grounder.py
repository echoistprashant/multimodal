"""Document Grounder Orchestrator.

Flattens extracted JSON payloads and grounds every scalar field and line item
against multi-page OCR/PDF tokens and reconstructed StructuredTables.
"""

from typing import Any, Dict, List, Optional
from app.grounding.aligner import find_matching_token_spans
from app.grounding.date_matcher import find_date_spans, parse_date_string
from app.grounding.numeric_matcher import find_numeric_spans
from app.grounding.schema import GroundingStatus, ProvenanceMatch
from app.grounding.table_grounder import ground_line_item_in_tables
from app.tables.grid_schema import StructuredTable


def _flatten_scalar_fields(payload: Dict[str, Any], prefix: str = "") -> List[tuple[str, Any]]:
    """Flatten nested dictionaries into dot-notation (field_path, value) pairs, skipping lists."""
    fields: List[tuple[str, Any]] = []
    for key, val in payload.items():
        if key in ("doc_type", "schema_version", "confidence_score", "metadata"):
            continue
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(val, dict):
            fields.extend(_flatten_scalar_fields(val, prefix=path))
        elif isinstance(val, list):
            continue
        elif val is not None and str(val).strip() != "":
            fields.append((path, val))
    return fields


class DocumentGrounder:
    """Maps extracted structured payloads back to spatial bounding-box evidence."""

    def ground_payload(
        self,
        extracted_data: Dict[str, Any],
        pages_tokens: Dict[int, List[dict]],
        tables: Optional[List[StructuredTable]] = None,
    ) -> List[ProvenanceMatch]:
        """Ground all scalar fields and line items across all document pages."""
        matches: List[ProvenanceMatch] = []

        # 1. Ground scalar fields
        for field_path, val in _flatten_scalar_fields(extracted_data):
            match = self._ground_scalar_field(field_path, val, pages_tokens)
            matches.append(match)

        # 2. Ground line items against tables or tokens
        line_items = extracted_data.get("line_items") or extracted_data.get("items") or []
        if isinstance(line_items, list):
            for idx, item in enumerate(line_items):
                if isinstance(item, dict):
                    item_match = ground_line_item_in_tables(idx, item, tables or [])
                    if not item_match.grounded and item.get("description"):
                        # Fallback to token span alignment across pages
                        fallback = self._ground_scalar_field(
                            f"line_items[{idx}]",
                            item["description"],
                            pages_tokens,
                        )
                        matches.append(fallback)
                    else:
                        matches.append(item_match)

        return matches

    def _ground_scalar_field(
        self,
        field_path: str,
        value: Any,
        pages_tokens: Dict[int, List[dict]],
    ) -> ProvenanceMatch:
        """Attempt numeric, date, exact, and fuzzy grounding across all pages."""
        best_spans = []

        # Numeric matching for int/float
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            for page_no, tokens in sorted(pages_tokens.items()):
                best_spans.extend(find_numeric_spans(float(value), tokens, page_no=page_no))
            if best_spans:
                return ProvenanceMatch(
                    field_path=field_path,
                    extracted_value=value,
                    status=GroundingStatus.NUMERIC,
                    grounded=True,
                    confidence=1.0,
                    best_span=best_spans[0],
                    candidate_spans=best_spans[:3],
                )

        str_val = str(value).strip()

        # Date matching if field looks like a date or parses as ISO date
        if "date" in field_path.lower() or parse_date_string(str_val):
            for page_no, tokens in sorted(pages_tokens.items()):
                best_spans.extend(find_date_spans(str_val, tokens, page_no=page_no))
            if best_spans:
                return ProvenanceMatch(
                    field_path=field_path,
                    extracted_value=value,
                    status=GroundingStatus.DATE,
                    grounded=True,
                    confidence=1.0,
                    best_span=best_spans[0],
                    candidate_spans=best_spans[:3],
                )

        # Textual exact/fuzzy sliding window alignment
        for page_no, tokens in sorted(pages_tokens.items()):
            best_spans.extend(find_matching_token_spans(str_val, tokens, page_no=page_no, min_similarity=0.78))

        best_spans.sort(key=lambda s: -s.match_score)
        if best_spans:
            top = best_spans[0]
            status = GroundingStatus.EXACT if top.match_score == 1.0 else GroundingStatus.FUZZY
            return ProvenanceMatch(
                field_path=field_path,
                extracted_value=value,
                status=status,
                grounded=True,
                confidence=top.match_score,
                best_span=top,
                candidate_spans=best_spans[:3],
            )

        return ProvenanceMatch(
            field_path=field_path,
            extracted_value=value,
            status=GroundingStatus.UNGROUNDED,
            grounded=False,
            confidence=0.0,
        )
