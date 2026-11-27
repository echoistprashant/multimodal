"""Grounding and Provenance Data Contracts.

Defines schemas for mapping extracted JSON fields back to exact page numbers,
normalized bounding boxes [x0, y0, x1, y1], and source OCR/PDF tokens.
"""

from enum import Enum
from typing import Any, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field


class GroundingStatus(str, Enum):
    """Verification state of an extracted field against document source tokens."""

    EXACT = "exact"          # Exact character/value match found on page
    FUZZY = "fuzzy"          # High-similarity OCR typo-tolerant match found
    NUMERIC = "numeric"      # Numerically equivalent match (e.g. $1,200.00 == 1200.0)
    DATE = "date"            # Calendar-equivalent date match (e.g. Nov 20, 2026 == 2026-11-20)
    UNGROUNDED = "ungrounded"  # No verifiable evidence found (potential hallucination)


class GroundedSpan(BaseModel):
    """A matched span of source tokens on a specific document page."""

    model_config = ConfigDict(frozen=True)

    page_no: int = Field(..., ge=1, description="1-based page number where evidence appears.")
    bbox: Tuple[float, float, float, float] = Field(
        ...,
        description="Merged normalized bounding box [x0, y0, x1, y1] in [0.0, 1.0].",
    )
    source_text: str = Field(..., description="Exact concatenated source text from matched tokens.")
    token_ids: List[str] = Field(default_factory=list, description="IDs of tokens forming this span.")
    match_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score in [0.0, 1.0].")


class ProvenanceMatch(BaseModel):
    """Complete provenance record for a single extracted entity field."""

    model_config = ConfigDict(frozen=True)

    field_path: str = Field(..., description="Dot-notation path (e.g. 'vendor.name', 'line_items[0].amount').")
    extracted_value: Any = Field(..., description="Extracted value from LLM/VLM.")
    status: GroundingStatus = Field(..., description="Grounding verification status.")
    grounded: bool = Field(..., description="True if field is verified in source document.")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Grounding match confidence.")
    best_span: Optional[GroundedSpan] = Field(default=None, description="Highest-scoring spatial evidence span.")
    candidate_spans: List[GroundedSpan] = Field(default_factory=list, description="Alternative candidate matches.")
