"""Semantic Layout Analysis Data Models and Enums.

Defines schemas for segmented layout blocks, hierarchical reading order,
and semantic block classifications (headers, paragraphs, tables, figures).
"""

import uuid
from enum import Enum
from typing import Any, Dict, List, Tuple
from pydantic import BaseModel, ConfigDict, Field


class SemanticBlockType(str, Enum):
    """Semantic functional role of a segmented block in a document page."""

    HEADER = "header"
    SUBHEADER = "subheader"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    LIST_ITEM = "list_item"
    FIGURE = "figure"
    CAPTION = "caption"
    FOOTER = "footer"
    UNKNOWN = "unknown"


class LayoutBlock(BaseModel):
    """Segmented structural block on a page with spatial coordinates and reading order."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: SemanticBlockType = Field(default=SemanticBlockType.PARAGRAPH)
    bbox: Tuple[float, float, float, float] = Field(
        ...,
        description="Normalized bounding box [x0, y0, x1, y1] where 0.0 <= x0 < x1 <= 1.0 and 0.0 <= y0 < y1 <= 1.0.",
    )
    reading_order: int = Field(
        ...,
        ge=0,
        description="Zero-indexed natural reading order position determined by layout analysis.",
    )
    text: str = Field(default="", description="Consolidated textual content of the block.")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    children_ids: List[str] = Field(
        default_factory=list,
        description="Child block or line token IDs contained within this block.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional auxiliary attributes (e.g. font size, heading level).",
    )
