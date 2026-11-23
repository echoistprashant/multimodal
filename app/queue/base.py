"""Background Task Queue Abstract Protocol.

Defines queue interface for dispatching long-running document processing jobs
(rendering, OCR, extraction, indexing) without blocking HTTP API request threads.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Protocol, runtime_checkable


@dataclass
class PipelineJob:
    """Represents a discrete document processing job in the queue."""

    job_id: str = field(default_factory=lambda: f"job_{uuid.uuid4().hex[:12]}")
    document_id: str = ""
    tenant_id: str = ""
    stage: str = "triage"
    status: Literal["queued", "processing", "completed", "failed"] = "queued"
    attempts: int = 0
    max_retries: int = 3
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class TaskQueue(Protocol):
    """Abstract protocol for background task scheduling and execution."""

    async def enqueue(self, job: PipelineJob) -> str:
        """Submit a pipeline job to the background queue. Returns job_id."""
        ...

    async def get_status(self, job_id: str) -> PipelineJob | None:
        """Fetch current status and progress of a scheduled job."""
        ...
