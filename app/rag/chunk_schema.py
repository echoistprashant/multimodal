"""Multimodal RAG Chunking Schemas and Modality Contracts."""

import uuid
from enum import Enum
from typing import Any, Dict, Tuple
from pydantic import BaseModel, ConfigDict, Field


class ChunkModality(str, Enum):
    """Modality category matching IndexItem database constraints."""

    TEXT = "text"
    TABLE_ROW = "table_row"
    FIGURE_DESC = "figure_desc"
    PAGE_IMAGE = "page_image"


class MultimodalChunk(BaseModel):
    """Atomic multimodal indexable unit with spatial grounding and tenant scope."""

    model_config = ConfigDict(frozen=True)

    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = Field(default="default-tenant")
    document_id: str
    page_no: int = Field(ge=1)
    modality: ChunkModality
    text: str = Field(..., description="Searchable textual or serialized representation.")
    bbox: Tuple[float, float, float, float] = Field(
        default=(0.0, 0.0, 1.0, 1.0),
        description="Normalized [x0, y0, x1, y1] region coordinates for visual citations.",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
