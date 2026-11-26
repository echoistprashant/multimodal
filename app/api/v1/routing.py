"""Routing Telemetry and Cost Analysis API Endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.routing_repo import RoutingRepository
from app.routing.telemetry import DocumentRoutingReport

router = APIRouter(prefix="/api/v1/documents", tags=["Routing Telemetry"])


@router.get(
    "/{document_id}/routing",
    response_model=DocumentRoutingReport,
    summary="Get document routing telemetry and cost savings report",
)
def get_document_routing_telemetry(
    document_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> DocumentRoutingReport:
    """Retrieve triage route assignments, latency statistics, and dollar savings for a processed document."""
    repo = RoutingRepository(db=db)
    report = repo.get_report(document_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Routing telemetry report not found for document '{document_id}'",
        )

    return report
