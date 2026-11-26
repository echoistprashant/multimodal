"""Routing Telemetry and Cost Analysis API Endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.routing_repo import RoutingRepository
from app.routing.telemetry import DocumentRoutingReport

router = APIRouter(prefix="/api/v1/documents", tags=["Routing Telemetry"])


@router.get(
    "/{document_id}/routing",
    response_model=DocumentRoutingReport,
    summary="Get document routing telemetry and cost savings report",
)
async def get_document_routing_telemetry(
    document_id: str,
    session: Optional[AsyncSession] = Depends(get_db_session),
) -> DocumentRoutingReport:
    """Retrieve triage route assignments, latency statistics, and dollar savings for a processed document."""
    repo = RoutingRepository()
    report = repo.get_report(document_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Routing telemetry report not found for document '{document_id}'",
        )

    return report
