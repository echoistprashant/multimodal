"""Automatic ReviewTask Generator for Human-in-the-Loop Queues."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.repositories.extraction_repo import StoredFieldRecord
from app.review.gateway_schema import ApprovalDecision, GatewayVerdict


class ReviewTaskItem(BaseModel):
    """Queued human review ticket for an anomalous or low-confidence field."""

    model_config = ConfigDict(frozen=False)

    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    field_id: str
    field_path: str
    original_value: object
    corrected_value: Optional[object] = None
    confidence: float
    bbox: List[float] = Field(default_factory=list)
    page_no: int = 1
    reason: str
    priority: int = Field(default=1, ge=1, le=5)
    status: str = Field(default="pending")  # pending | resolved | dismissed
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None


def generate_review_tasks(
    verdict: GatewayVerdict,
    fields: List[StoredFieldRecord],
) -> List[ReviewTaskItem]:
    """Create prioritized ReviewTaskItem tickets for flagged fields."""
    if verdict.decision == ApprovalDecision.AUTO_APPROVED:
        return []

    flagged_set = set(verdict.flagged_fields)
    tasks: List[ReviewTaskItem] = []

    for field in fields:
        if field.field_path in flagged_set or not field.grounded:
            priority = 1 if not field.grounded else 2
            tasks.append(
                ReviewTaskItem(
                    document_id=verdict.document_id,
                    field_id=field.field_id,
                    field_path=field.field_path,
                    original_value=field.value,
                    confidence=field.confidence,
                    bbox=field.bbox,
                    page_no=field.page_no,
                    reason="; ".join(verdict.reasons) or "Flagged for human verification.",
                    priority=priority,
                )
            )

    return tasks
