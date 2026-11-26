"""Table Detection Data Models and Boundary Contracts.

Defines schemas for tabular regions, structural table classifications
(bordered vs borderless), and spatial bounding limits.
"""

import uuid
from enum import Enum
from typing import List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field


class TableType(str, Enum):
    """Structural visual type of a detected table."""

    BORDERED = "bordered"      # Grid with explicit horizontal and vertical divider lines
    BORDERLESS = "borderless"  # Tabular alignment separated by whitespace gutters
    PARTIAL = "partial"        # Underlined headers or horizontal rules only


class TableBoundary(BaseModel):
    """Spatial coordinates and structural parameters of a table region."""

    model_config = ConfigDict(frozen=True)

    bbox: Tuple[float, float, float, float] = Field(
        ...,
        description="Normalized table bounding box [x0, y0, x1, y1] in [0.0, 1.0].",
    )
    table_type: TableType = Field(default=TableType.BORDERED)
    confidence: float = Field(default=0.90, ge=0.0, le=1.0)
    row_count_estimate: int = Field(default=1, ge=1)
    col_count_estimate: int = Field(default=1, ge=1)


class TableRegion(BaseModel):
    """Full table detection container including coordinate boundaries and divider lines."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    page_number: int = Field(default=1, ge=1)
    boundary: TableBoundary
    horizontal_lines: List[Tuple[float, float, float, float]] = Field(
        default_factory=list,
        description="List of normalized horizontal line segments [x0, y, x1, y].",
    )
    vertical_lines: List[Tuple[float, float, float, float]] = Field(
        default_factory=list,
        description="List of normalized vertical line segments [x, y0, x, y1].",
    )
    caption: Optional[str] = Field(default=None, description="Inferred table caption or header text.")
