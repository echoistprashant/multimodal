"""Observability Metrics API Endpoint."""

from typing import Any, Dict
from fastapi import APIRouter

from app.observability.metrics import MetricsCollector

router = APIRouter(prefix="/api/v1/metrics", tags=["Observability"])


@router.get(
    "",
    response_model=Dict[str, Any],
    summary="Get pipeline observability counters and stage latency histograms",
)
def get_metrics() -> Dict[str, Any]:
    """Return live operational counters and p95 latency statistics across pipeline stages."""
    return MetricsCollector.get_instance().snapshot()
