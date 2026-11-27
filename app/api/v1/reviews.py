"""Human-in-the-Loop Review Queue API Endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status

from app.repositories.review_repo import ReviewQueueRepository
from app.review.task_generator import ReviewTaskItem
from app.schemas.review import FieldCorrectionRequest, ReviewQueueListResponse

router = APIRouter(prefix="/api/v1/reviews", tags=["Human Review Queue"])


@router.get(
    "",
    response_model=ReviewQueueListResponse,
    summary="List pending or resolved human review tasks",
)
def list_review_tasks(
    task_status: Optional[str] = "pending",
    document_id: Optional[str] = None,
) -> ReviewQueueListResponse:
    """Retrieve prioritized human review tasks filtered by status or document ID."""
    repo = ReviewQueueRepository()
    tasks = repo.list_tasks(status=task_status, document_id=document_id)
    return ReviewQueueListResponse(total=len(tasks), items=tasks)


@router.post(
    "/{task_id}/resolve",
    response_model=ReviewTaskItem,
    summary="Resolve a flagged review task with corrected field value",
)
def resolve_review_task(
    task_id: str,
    body: FieldCorrectionRequest,
) -> ReviewTaskItem:
    """Apply human correction and mark the review ticket as resolved."""
    repo = ReviewQueueRepository()
    updated = repo.resolve_task(
        task_id=task_id,
        corrected_value=body.corrected_value,
        reviewer=body.reviewer,
        notes=body.notes,
        dismiss=body.dismiss,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review task '{task_id}' not found.",
        )
    return updated
