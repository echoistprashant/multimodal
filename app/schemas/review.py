"""API Request/Response Schemas for Human-in-the-Loop Review Queue."""

from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class FieldCorrectionRequest(BaseModel):
    """Payload submitted by a human reviewer to resolve a flagged field."""

    model_config = ConfigDict(frozen=True)

    corrected_value: Any = Field(..., description="Verified ground-truth value.")
    reviewer: str = Field(default="reviewer-1", description="Reviewer username or ID.")
    notes: Optional[str] = Field(default=None, description="Optional audit comment.")
    dismiss: bool = Field(default=False, description="Set True to dismiss false-positive alert.")


class ReviewQueueListResponse(BaseModel):
    """Paginated/filtered list of review tasks."""

    model_config = ConfigDict(frozen=True)

    total: int = Field(ge=0)
    items: List[Any] = Field(default_factory=list)
