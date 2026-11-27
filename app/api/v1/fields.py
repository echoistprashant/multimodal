"""Extracted Fields and Visual Provenance API Endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, status

from app.repositories.extraction_repo import ExtractionRepository, StoredFieldRecord

router = APIRouter(prefix="/api/v1/documents", tags=["Extracted Fields & Provenance"])


@router.get(
    "/{document_id}/fields",
    response_model=List[StoredFieldRecord],
    summary="Get extracted fields with bounding-box provenance",
)
def get_document_fields(document_id: str) -> List[StoredFieldRecord]:
    """Retrieve all extracted entity fields, grounding flags, and [x0, y0, x1, y1] highlight boxes."""
    repo = ExtractionRepository()
    fields = repo.get_fields(document_id)
    if not fields:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No extracted fields found for document '{document_id}'",
        )
    return fields
