"""Repository for Human-in-the-Loop Review Queue Management."""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.core.logging import get_logger
from app.review.task_generator import ReviewTaskItem

logger = get_logger("app.repositories.review_repo")

_REVIEW_TASKS_STORE: Dict[str, ReviewTaskItem] = {}


class ReviewQueueRepository:
    """Data access repository managing pending and resolved review tasks."""

    def enqueue_tasks(self, tasks: List[ReviewTaskItem]) -> None:
        """Insert generated review tasks into the queue."""
        for t in tasks:
            _REVIEW_TASKS_STORE[t.task_id] = t
        logger.info(f"Enqueued {len(tasks)} review task(s) into HITL queue.")

    def list_tasks(
        self,
        status: Optional[str] = "pending",
        document_id: Optional[str] = None,
    ) -> List[ReviewTaskItem]:
        """List review tasks filtered by status and/or document_id, sorted by priority."""
        items = list(_REVIEW_TASKS_STORE.values())
        if status:
            items = [t for t in items if t.status == status]
        if document_id:
            items = [t for t in items if t.document_id == document_id]
        items.sort(key=lambda t: (t.priority, t.created_at))
        return items

    def get_task(self, task_id: str) -> Optional[ReviewTaskItem]:
        """Fetch a single review task by ID."""
        return _REVIEW_TASKS_STORE.get(task_id)

    def resolve_task(
        self,
        task_id: str,
        corrected_value: object,
        reviewer: str = "human_reviewer",
        notes: Optional[str] = None,
        dismiss: bool = False,
    ) -> Optional[ReviewTaskItem]:
        """Resolve or dismiss a review task with a human-verified value."""
        task = _REVIEW_TASKS_STORE.get(task_id)
        if not task:
            return None

        task.corrected_value = corrected_value
        task.status = "dismissed" if dismiss else "resolved"
        task.assigned_to = reviewer
        task.resolution_notes = notes
        task.resolved_at = datetime.now(timezone.utc)
        _REVIEW_TASKS_STORE[task_id] = task
        logger.info(f"Review task {task_id} marked '{task.status}' by {reviewer}.")
        return task

    def clear_cache(self) -> None:
        """Clear in-memory store for test isolation."""
        _REVIEW_TASKS_STORE.clear()
