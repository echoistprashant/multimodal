"""Documents API Router.

Handles document upload, metadata inspection, pagination, and deletion endpoints.
"""

import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.validation import FileValidationError
from app.db.session import get_db_session
from app.queue.base import PipelineJob
from app.queue.dispatcher import get_task_queue
from app.schemas.document import DocumentUploadResponse
from app.services.ingest_service import DocumentIngestService
from app.storage.s3 import get_storage_provider

logger = get_logger("app.api.v1.documents")
router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload Document for Ingestion",
)
async def upload_document(
    file: Annotated[UploadFile, File(..., description="Document file (PDF, PNG, JPG, TIFF)")],
    x_tenant_id: Annotated[str, Header(description="Tenant scope identifier")] = "default-tenant",
    session: AsyncSession = Depends(get_db_session),
) -> DocumentUploadResponse:
    """Asynchronously ingest and queue a document for multimodal processing."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename must not be empty",
        )

    content = await file.read()
    storage = get_storage_provider()
    ingest_service = DocumentIngestService(session=session, storage=storage)

    try:
        result = await ingest_service.ingest_document(
            tenant_id=x_tenant_id,
            filename=file.filename,
            content=content,
        )
    except FileValidationError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as err:
        logger.error(f"Unexpected error during document ingestion: {err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal document ingestion failure",
        )

    # Dispatch to background task queue if not an existing duplicate
    if not result.is_duplicate:
        queue = get_task_queue()
        job = PipelineJob(
            document_id=str(result.document.id),
            tenant_id=x_tenant_id,
            stage="render",
            payload={"filename": result.document.filename},
        )
        await queue.enqueue(job)

    return DocumentUploadResponse(
        id=result.document.id,
        filename=result.document.filename,
        mime_type=result.document.mime_type,
        sha256=result.document.sha256,
        status=result.document.status,  # type: ignore[arg-type]
        is_duplicate=result.is_duplicate,
        created_at=result.document.created_at,
    )
