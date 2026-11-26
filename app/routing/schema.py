"""Routing Schemas, Enums, and Policy Contracts.

Defines the multi-tier triage decision contracts balancing cost, latency,
and document fidelity across native parsing, local OCR, and VLM vision pipelines.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RouteType(str, Enum):
    """Execution pathway for processing a document page."""

    NATIVE = "native"      # Zero compute cost: direct PDF text extraction
    OCR = "ocr"            # Low compute cost: local Tesseract/OCR engine
    VLM = "vlm"            # High fidelity/multimodal: vision-language model
    FALLBACK = "fallback"  # Emergency recovery route when preferred tier fails


class RoutingPolicy(BaseModel):
    """Configurable routing thresholds and cost governance constraints."""

    model_config = ConfigDict(frozen=True)

    min_text_health_threshold: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Minimum text layer health score required to qualify for native parsing.",
    )
    max_visual_complexity_for_ocr: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Maximum visual complexity score allowable before escalating to VLM.",
    )
    max_cost_per_page_usd: float = Field(
        default=0.02,
        ge=0.0,
        description="Budget ceiling per page in USD.",
    )
    prefer_free_local_engine: bool = Field(
        default=True,
        description="Whether to prioritize free zero-cost open-source engines over cloud APIs.",
    )
    forced_route: Optional[RouteType] = Field(
        default=None,
        description="Manual override route forcing a specific execution pathway.",
    )


class EstimatedCost(BaseModel):
    """Estimated resource expenditure and financial cost for a routing tier."""

    model_config = ConfigDict(frozen=True)

    route: RouteType
    usd_cost: float = Field(ge=0.0, description="Estimated monetary cost in USD.")
    latency_ms: float = Field(ge=0.0, description="Expected wall-clock latency in milliseconds.")
    free_tier_eligible: bool = Field(
        default=True,
        description="Whether this route operates 100% free of cloud API fees.",
    )


class RouteDecision(BaseModel):
    """Deterministic routing decision for a page or document."""

    model_config = ConfigDict(frozen=True)

    route: RouteType
    confidence: float = Field(ge=0.0, le=1.0, description="Routing confidence score.")
    reason: str = Field(..., description="Explanation of why this pathway was chosen.")
    cost_estimate: EstimatedCost
    text_health_score: float = Field(ge=0.0, le=1.0)
    visual_complexity_score: float = Field(ge=0.0, le=1.0)
