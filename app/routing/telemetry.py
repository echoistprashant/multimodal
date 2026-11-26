"""Routing Telemetry and Financial Savings Accumulator.

Tracks per-page execution routes, calculates aggregate cost accounting,
and records operational telemetry across document processing runs.
"""

from typing import Dict
from pydantic import BaseModel, ConfigDict, Field

from app.routing.cost_estimator import calculate_batch_cost_savings
from app.routing.schema import RouteDecision, RouteType


class DocumentRoutingReport(BaseModel):
    """Aggregate routing telemetry and cost analytics for an entire document."""

    model_config = ConfigDict(frozen=True)

    document_id: str
    total_pages: int = Field(ge=0)
    native_page_count: int = Field(ge=0)
    ocr_page_count: int = Field(ge=0)
    vlm_page_count: int = Field(ge=0)
    total_cost_usd: float = Field(ge=0.0)
    unoptimized_cost_usd: float = Field(ge=0.0)
    estimated_savings_usd: float = Field(ge=0.0)
    savings_percentage: float = Field(ge=0.0, le=100.0)
    page_decisions: Dict[int, RouteDecision] = Field(default_factory=dict)


class RoutingTelemetryAccumulator:
    """Thread-safe collector aggregating route decisions for a document processing job."""

    def __init__(self, document_id: str) -> None:
        self.document_id = document_id
        self._decisions: dict[int, RouteDecision] = {}

    def record_decision(self, page_number: int, decision: RouteDecision) -> None:
        """Record the routing decision for a specific page."""
        self._decisions[page_number] = decision

    @property
    def decisions(self) -> dict[int, RouteDecision]:
        """Return a copy of all recorded page decisions."""
        return dict(self._decisions)

    def generate_report(self) -> DocumentRoutingReport:
        """Compile complete document routing summary and cost savings report."""
        total_pages = len(self._decisions)
        native_count = sum(1 for d in self._decisions.values() if d.route == RouteType.NATIVE)
        ocr_count = sum(1 for d in self._decisions.values() if d.route == RouteType.OCR)
        vlm_count = sum(1 for d in self._decisions.values() if d.route == RouteType.VLM)

        savings = calculate_batch_cost_savings(list(self._decisions.values()))

        return DocumentRoutingReport(
            document_id=self.document_id,
            total_pages=total_pages,
            native_page_count=native_count,
            ocr_page_count=ocr_count,
            vlm_page_count=vlm_count,
            total_cost_usd=savings["actual_cost_usd"],
            unoptimized_cost_usd=savings["unoptimized_cost_usd"],
            estimated_savings_usd=savings["saved_usd"],
            savings_percentage=savings["savings_percentage"],
            page_decisions=dict(self._decisions),
        )
