"""Numeric and Currency Equivalence Matcher for Provenance Grounding.

Matches extracted float values (e.g., 1250.0) back to formatted currency tokens
in the source document (e.g., "$1,250.00", "EUR 1.250,00", "USD 1250").
"""

import re
from typing import List, Optional, Sequence
from app.grounding.bbox_merger import merge_bounding_boxes
from app.grounding.schema import GroundedSpan

NUMBER_TOKEN_RE = re.compile(r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")


def parse_numeric_token(raw_text: str) -> Optional[float]:
    """Extract numeric float value from formatted currency or number string."""
    cleaned = raw_text.replace("$", "").replace("€", "").replace("£", "").replace("₹", "").strip()
    match = NUMBER_TOKEN_RE.search(cleaned)
    if not match:
        return None
    try:
        return float(match.group(0).replace(",", ""))
    except ValueError:
        return None


def find_numeric_spans(
    target_value: float,
    page_tokens: Sequence[dict],
    page_no: int = 1,
    tolerance: float = 0.01,
) -> List[GroundedSpan]:
    """Locate page tokens whose parsed numeric value equals target_value within tolerance."""
    matches: List[GroundedSpan] = []

    for idx, tok in enumerate(page_tokens):
        raw_txt = str(tok.get("text", "")).strip()
        if not raw_txt:
            continue
        parsed = parse_numeric_token(raw_txt)
        if parsed is not None and abs(parsed - target_value) <= tolerance:
            bbox = tuple(tok["bbox"]) if "bbox" in tok else (0.0, 0.0, 0.0, 0.0)
            matches.append(
                GroundedSpan(
                    page_no=page_no,
                    bbox=merge_bounding_boxes([bbox]),  # type: ignore[list-item]
                    source_text=raw_txt,
                    token_ids=[str(tok.get("id", f"tok_{idx}"))],
                    match_score=1.0,
                )
            )

    return matches
