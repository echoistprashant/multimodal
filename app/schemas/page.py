"""Page and Block Inspection DTO Schemas Module."""

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class BlockSummaryResponse(BaseModel):
    """Layout block summary schema."""

    id: uuid.UUID
    type: str
    reading_order: int
    bbox: list[float] = Field(..., description="[x0, y0, x1, y1] normalized coordinates")
    text: str

    model_config = ConfigDict(from_attributes=True)


class PageDetailResponse(BaseModel):
    """Detailed page inspection schema with image link and detected blocks."""

    id: uuid.UUID
    document_id: uuid.UUID
    page_no: int
    width_px: int
    height_px: int
    dpi: int
    route: str | None = None
    quality_score: float | None = None
    rotation: int = 0
    image_url: str | None = None
    blocks: list[BlockSummaryResponse] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
