"""Date Format Normalizer and Calendar Provenance Matcher.

Matches ISO-8601 extracted dates (YYYY-MM-DD) against diverse source document
date formats (e.g., 'Nov 20, 2026', '20/11/2026', '11-20-2026').
"""

from datetime import datetime
from typing import List, Optional, Sequence
from app.grounding.bbox_merger import merge_bounding_boxes
from app.grounding.schema import GroundedSpan

COMMON_DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%m-%d-%Y",
    "%m/%d/%Y",
    "%b %d, %Y",
    "%B %d, %Y",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d %Y",
]


def parse_date_string(raw_text: str) -> Optional[str]:
    """Parse common date formats into canonical ISO-8601 YYYY-MM-DD string."""
    cleaned = raw_text.strip().rstrip(".,;:")
    for fmt in COMMON_DATE_FORMATS:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def find_date_spans(
    target_iso_date: str,
    page_tokens: Sequence[dict],
    page_no: int = 1,
) -> List[GroundedSpan]:
    """Locate single or multi-token date spans matching target_iso_date."""
    canonical_target = parse_date_string(target_iso_date) or target_iso_date.strip()
    matches: List[GroundedSpan] = []

    for start_idx in range(len(page_tokens)):
        # Check 1-token to 3-token windows (e.g. 'Nov' '20,' '2026')
        for win_len in (1, 2, 3):
            end_idx = start_idx + win_len
            if end_idx > len(page_tokens):
                break
            window = page_tokens[start_idx:end_idx]
            win_text = " ".join(str(t.get("text", "")).strip() for t in window).strip()
            parsed = parse_date_string(win_text)
            if parsed == canonical_target:
                boxes = [tuple(t["bbox"]) for t in window if "bbox" in t]
                matches.append(
                    GroundedSpan(
                        page_no=page_no,
                        bbox=merge_bounding_boxes(boxes),  # type: ignore[arg-type]
                        source_text=win_text,
                        token_ids=[str(t.get("id", f"tok_{start_idx + i}")) for i, t in enumerate(window)],
                        match_score=1.0,
                    )
                )
                break

    return matches
