"""Auto-Approval Gateway and Straight-Through Processing (STP) Schemas."""

from enum import Enum
from typing import List
from pydantic import BaseModel, ConfigDict, Field


class ApprovalDecision(str, Enum):
    """Gateway routing verdict after validation and confidence checks."""

    AUTO_APPROVED = "auto_approved"        # Straight-Through Processing (no human needed)
    NEEDS_REVIEW = "needs_review"          # Routed to human-in-the-loop review queue
    REJECTED = "rejected"                  # Severely corrupted or unparseable document


class STPPolicy(BaseModel):
    """Configurable thresholds governing Straight-Through Processing (STP)."""

    model_config = ConfigDict(frozen=True)

    min_composite_confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    min_field_confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    require_zero_validation_errors: bool = Field(default=True)
    require_all_critical_grounded: bool = Field(default=True)


class GatewayVerdict(BaseModel):
    """Final auto-approval or human-review decision with explicit audit reasons."""

    model_config = ConfigDict(frozen=True)

    document_id: str
    decision: ApprovalDecision
    composite_confidence: float = Field(ge=0.0, le=1.0)
    reasons: List[str] = Field(default_factory=list)
    flagged_fields: List[str] = Field(default_factory=list)
