"""Pipeline Stage Tracer for Per-Stage Latency and Cost Spans."""

import time
from contextlib import contextmanager
from typing import Iterator, List
from pydantic import BaseModel, ConfigDict

from app.observability.metrics import MetricsCollector


class StageSpan(BaseModel):
    """Execution trace span for a single pipeline stage."""

    model_config = ConfigDict(frozen=True)

    stage_name: str
    latency_ms: float
    status: str = "ok"


class PipelineStageTracer:
    """Collects ordered stage spans for a document processing run."""

    def __init__(self, document_id: str) -> None:
        self.document_id = document_id
        self.spans: List[StageSpan] = []
        self._metrics = MetricsCollector.get_instance()

    @contextmanager
    def trace_stage(self, stage_name: str) -> Iterator[None]:
        start = time.perf_counter()
        status = "ok"
        try:
            yield
        except Exception:
            status = "error"
            raise
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            self.spans.append(StageSpan(stage_name=stage_name, latency_ms=elapsed_ms, status=status))
            self._metrics.record_latency(stage_name, elapsed_ms)
            self._metrics.increment(f"stage.{stage_name}.{status}")
