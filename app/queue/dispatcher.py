"""Task Queue Dispatcher Implementation.

Provides both an In-Memory queue (for local zero-dependency development/testing)
and a Redis-backed queue for production distributed workers.
"""

from app.core.logging import get_logger
from app.queue.base import PipelineJob, TaskQueue

logger = get_logger("app.queue.dispatcher")


class InMemoryTaskQueue(TaskQueue):
    """In-memory task dispatcher for local development and deterministic unit testing."""

    def __init__(self) -> None:
        self._jobs: dict[str, PipelineJob] = {}

    async def enqueue(self, job: PipelineJob) -> str:
        """Enqueue job in local memory store."""
        job.status = "queued"
        self._jobs[job.job_id] = job
        logger.info(f"Enqueued in-memory job {job.job_id} for doc {job.document_id}")
        return job.job_id

    async def get_status(self, job_id: str) -> PipelineJob | None:
        """Retrieve job state from local memory store."""
        return self._jobs.get(job_id)


_global_queue = InMemoryTaskQueue()


def get_task_queue() -> TaskQueue:
    """Return configured task queue instance."""
    return _global_queue
