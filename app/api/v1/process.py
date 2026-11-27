"""Master End-to-End Pipeline Trigger API Endpoint."""

from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.pipeline.master_orchestrator import MasterPipelineOrchestrator
from app.pipeline.orchestrator_schema import (
    FullPipelineResult,
    PipelineExecutionConfig,
    PipelinePageInput,
)

router = APIRouter(prefix="/api/v1/documents", tags=["Pipeline Orchestration"])


class ProcessDocumentRequest(BaseModel):
    """Request payload for running the end-to-end multimodal pipeline on page inputs."""

    model_config = ConfigDict(frozen=True)

    pages: List[PipelinePageInput] = Field(..., min_length=1)
    config: Optional[PipelineExecutionConfig] = Field(default=None)


@router.post(
    "/{document_id}/process",
    response_model=FullPipelineResult,
    summary="Execute full end-to-end MDIS pipeline (Triage -> Layout -> Extraction -> Grounding -> Validation -> RAG)",
)
async def process_document_pipeline(
    document_id: str,
    body: ProcessDocumentRequest,
) -> FullPipelineResult:
    """Run the complete multimodal document intelligence pipeline on provided page tokens."""
    orchestrator = MasterPipelineOrchestrator()
    return await orchestrator.run(
        document_id=document_id,
        pages=body.pages,
        config=body.config,
    )
