"""Hallucination Audit Schemas and Grounding Policy Contracts."""

from typing import List
from pydantic import BaseModel, ConfigDict, Field


class GroundingAuditPolicy(BaseModel):
    """Policy governing hallucination severity and critical fields requiring strict grounding."""

    model_config = ConfigDict(frozen=True)

    critical_fields: List[str] = Field(
        default_factory=lambda: ["invoice_number", "total_amount", "vendor.name", "merchant_name", "patient_name"],
        description="Fields whose ungrounded extraction triggers mandatory human review.",
    )
    max_allowed_ungrounded_ratio: float = Field(
        default=0.20,
        ge=0.0,
        le=1.0,
        description="Maximum acceptable fraction of ungrounded fields before flagging the entire document.",
    )


class HallucinationReport(BaseModel):
    """Audit report summarizing grounded vs. ungrounded fields and hallucination risk."""

    model_config = ConfigDict(frozen=True)

    document_id: str
    total_fields_checked: int = Field(ge=0)
    grounded_count: int = Field(ge=0)
    ungrounded_count: int = Field(ge=0)
    ungrounded_fields: List[str] = Field(default_factory=list)
    critical_ungrounded_fields: List[str] = Field(default_factory=list)
    hallucination_rate: float = Field(ge=0.0, le=1.0)
    requires_human_review: bool = Field(default=False)
