"""Structured Table Grid Schemas and Cell Hierarchy.

Defines cell coordinate schemas, row models, column spans, and full structured table models.
"""

import uuid
from typing import List, Tuple
from pydantic import BaseModel, ConfigDict, Field


class TableCell(BaseModel):
    """An individual cell within a structured table matrix."""

    model_config = ConfigDict(frozen=True)

    cell_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    row_idx: int = Field(..., ge=0, description="0-based row index.")
    col_idx: int = Field(..., ge=0, description="0-based column index.")
    row_span: int = Field(default=1, ge=1, description="Number of rows spanned by this cell.")
    col_span: int = Field(default=1, ge=1, description="Number of columns spanned by this cell.")
    text: str = Field(default="", description="Text content contained within the cell.")
    bbox: Tuple[float, float, float, float] = Field(
        ...,
        description="Normalized [x0, y0, x1, y1] coordinates of the cell bounds.",
    )
    is_header: bool = Field(default=False, description="Whether this cell acts as a column or row header.")


class TableRow(BaseModel):
    """Row in a structured table containing an ordered sequence of cells."""

    model_config = ConfigDict(frozen=True)

    row_idx: int = Field(..., ge=0)
    cells: List[TableCell] = Field(default_factory=list)
    is_header_row: bool = Field(default=False)


class StructuredTable(BaseModel):
    """Full two-dimensional structured table object with reconstructed cells and inferred headers."""

    model_config = ConfigDict(frozen=True)

    table_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    page_number: int = Field(default=1, ge=1)
    bbox: Tuple[float, float, float, float] = Field(
        ...,
        description="Bounding box enclosing the entire structured table.",
    )
    num_rows: int = Field(..., ge=0)
    num_cols: int = Field(..., ge=0)
    headers: List[str] = Field(default_factory=list, description="Extracted column header labels.")
    rows: List[TableRow] = Field(default_factory=list)
