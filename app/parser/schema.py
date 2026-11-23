"""Document Parser Data Contracts and Coordinate Models.

Defines normalized bounding boxes, tokens, and unified page extraction contracts
shared across native PDF parsers, OCR engines, and VLM extractors.
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class BoundingBox:
    """Normalized spatial bounding box: coordinates are in fractional range [0.0, 1.0]."""

    x0: float  # Left
    y0: float  # Top
    x1: float  # Right
    y1: float  # Bottom

    def to_list(self) -> list[float]:
        """Convert to JSON serializable list [x0, y0, x1, y1]."""
        return [round(self.x0, 4), round(self.y0, 4), round(self.x1, 4), round(self.y1, 4)]

    @classmethod
    def from_list(cls, coords: list[float]) -> "BoundingBox":
        """Instantiate BoundingBox from 4-element coordinate list."""
        if len(coords) != 4:
            raise ValueError(f"Bounding box must contain exactly 4 coordinates, got {coords}")
        return cls(x0=coords[0], y0=coords[1], x1=coords[2], y1=coords[3])


@dataclass
class Token:
    """Individual extracted text unit (word/token) with spatial position and confidence."""

    text: str
    bbox: BoundingBox
    confidence: float = 1.0
    page_no: int = 1
    source: Literal["native", "ocr", "vlm"] = "native"


@dataclass
class PageParseResult:
    """Consolidated parse output for a single document page."""

    page_no: int
    width_pt: float
    height_pt: float
    tokens: list[Token] = field(default_factory=list)
    raw_text: str = ""
    has_text_layer: bool = False
