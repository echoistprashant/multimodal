"""Composite Confidence Scoring and Calibration Schemas."""

from typing import Dict
from pydantic import BaseModel, ConfigDict, Field


class CalibrationWeights(BaseModel):
    """Weights combining multi-signal extraction reliability indicators."""

    model_config = ConfigDict(frozen=True)

    ocr_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    model_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    grounding_weight: float = Field(default=0.30, ge=0.0, le=1.0)
    validation_weight: float = Field(default=0.20, ge=0.0, le=1.0)


class ConfidenceBreakdown(BaseModel):
    """Decomposed confidence metrics for an extracted document or field."""

    model_config = ConfigDict(frozen=True)

    ocr_confidence: float = Field(ge=0.0, le=1.0)
    model_confidence: float = Field(ge=0.0, le=1.0)
    grounding_confidence: float = Field(ge=0.0, le=1.0)
    validation_score: float = Field(ge=0.0, le=1.0)
    raw_composite_score: float = Field(ge=0.0, le=1.0)
    calibrated_score: float = Field(ge=0.0, le=1.0)
    field_scores: Dict[str, float] = Field(default_factory=dict)
