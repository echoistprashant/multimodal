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
from app.schemas.document import (
    DocumentListResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
)
from app.services.ingest_service import DocumentIngestService
from app.storage.s3 import get_storage_provider

logger = get_logger("app.api.v1.documents")
router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


@router.get(
    "/{document_id}",
    response_model=DocumentStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Document Status and Metadata",
)
async def get_document(
    document_id: uuid.UUID,
    x_tenant_id: Annotated[str, Header(description="Tenant scope identifier")] = "default-tenant",
    session: AsyncSession = Depends(get_db_session),
) -> DocumentStatusResponse:
    """Retrieve processing status and extracted attributes for a document."""
    from app.repositories.document_repo import DocumentRepository

    repo = DocumentRepository(session)
    doc = await repo.get_by_id(document_id=document_id, tenant_id=x_tenant_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found for tenant {x_tenant_id}",
        )

    return DocumentStatusResponse(
        id=doc.id,
        tenant_id=doc.tenant_id,
        filename=doc.filename,
        mime_type=doc.mime_type,
        sha256=doc.sha256,
        page_count=doc.page_count,
        doc_type=doc.doc_type,
        doc_type_confidence=doc.doc_type_confidence,
        status=doc.status,
        pipeline_version=doc.pipeline_version,
        error_message=doc.error_message,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Ingested Documents",
)
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    doc_status: str | None = None,
    x_tenant_id: Annotated[str, Header(description="Tenant scope identifier")] = "default-tenant",
    session: AsyncSession = Depends(get_db_session),
) -> DocumentListResponse:
    """Retrieve paginated documents for the tenant."""
    from app.repositories.document_repo import DocumentRepository

    repo = DocumentRepository(session)
    docs = await repo.list_documents(
        tenant_id=x_tenant_id,
        skip=skip,
        limit=limit,
        status=doc_status,
    )

    items = [
        DocumentStatusResponse(
            id=d.id,
            tenant_id=d.tenant_id,
            filename=d.filename,
            mime_type=d.mime_type,
            sha256=d.sha256,
            page_count=d.page_count,
            doc_type=d.doc_type,
            doc_type_confidence=d.doc_type_confidence,
            status=d.status,
            pipeline_version=d.pipeline_version,
            error_message=d.error_message,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in docs
    ]

    return DocumentListResponse(
        items=items,
        total=len(items),
        skip=skip,
        limit=limit,
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Document",
)
async def delete_document(
    document_id: uuid.UUID,
    x_tenant_id: Annotated[str, Header(description="Tenant scope identifier")] = "default-tenant",
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete document and all associated pages, layout blocks, and extracted fields."""
    from app.repositories.document_repo import DocumentRepository

    repo = DocumentRepository(session)
    doc = await repo.get_by_id(document_id=document_id, tenant_id=x_tenant_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found for tenant {x_tenant_id}",
        )

    # Clean up storage payload
    storage = get_storage_provider()
    await storage.delete_object(doc.storage_key)

    # Cascade delete in database
    await repo.delete(document_id=document_id, tenant_id=x_tenant_id)
    await session.commit()



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
