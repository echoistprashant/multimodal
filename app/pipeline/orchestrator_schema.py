"""Master End-to-End Pipeline Orchestrator Schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.observability.tracer import StageSpan
from app.review.gateway_schema import ApprovalDecision
from app.routing.telemetry import DocumentRoutingReport


class PipelinePageInput(BaseModel):
    """Input representation of a rendered/parsed page entering the master pipeline."""

    model_config = ConfigDict(frozen=True)

    page_no: int = Field(ge=1)
    tokens: List[dict] = Field(default_factory=list)
    raw_text: str = Field(default="")


class PipelineExecutionConfig(BaseModel):
    """Execution flags controlling end-to-end pipeline stages."""

    model_config = ConfigDict(frozen=True)

    tenant_id: str = Field(default="default-tenant")
    forced_doc_type: Optional[str] = Field(default=None)
    enable_rag_indexing: bool = Field(default=True)


class FullPipelineResult(BaseModel):
    """Unified output of running a document through all MDIS pipeline stages."""

    model_config = ConfigDict(frozen=True)

    document_id: str
    doc_type: str
    approval_decision: ApprovalDecision
    composite_confidence: float = Field(ge=0.0, le=1.0)
    hallucination_rate: float = Field(ge=0.0, le=1.0)
    chunks_indexed: int = Field(ge=0)
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    routing_report: Optional[DocumentRoutingReport] = None
    stage_traces: List[StageSpan] = Field(default_factory=list)
