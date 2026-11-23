"""Document Pydantic DTO Schemas Module.

Provides request/response schemas for document upload, status polling,
pagination, and metadata inspection.
"""

import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class DocumentUploadResponse(BaseModel):
    """Response returned upon successful asynchronous document upload ingestion."""

    id: uuid.UUID = Field(..., description="Unique document ID")
    filename: str = Field(..., description="Original uploaded filename")
    mime_type: str = Field(..., description="Verified MIME type")
    sha256: str = Field(..., description="SHA-256 fingerprint")
    status: Literal["uploaded", "processing", "needs_review", "approved", "failed"] = Field(
        default="uploaded",
        description="Ingestion status",
    )
    is_duplicate: bool = Field(
        default=False,
        description="True if document content was previously uploaded (idempotent deduplication)",
    )
    created_at: datetime = Field(..., description="Timestamp of document registration")

    model_config = ConfigDict(from_attributes=True)


class DocumentStatusResponse(BaseModel):
    """Detailed status and extraction summary for a specific document."""

    id: uuid.UUID
    tenant_id: str
    filename: str
    mime_type: str
    sha256: str
    page_count: int
    doc_type: str | None = None
    doc_type_confidence: float | None = None
    status: str
    pipeline_version: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """Paginated list of document summaries."""

    items: list[DocumentStatusResponse]
    total: int = Field(..., description="Total items available")
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=100)
