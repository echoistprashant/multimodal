"""Repository for Persisting and Retrieving Document Routing Telemetry.

Manages relational database storage and in-memory caching for route decisions,
cost tracking metrics, and savings analytics.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.document import Document
from app.routing.telemetry import DocumentRoutingReport

logger = get_logger("app.repositories.routing_repo")

# In-memory fast cache for active job telemetry
_TELEMETRY_CACHE: dict[str, DocumentRoutingReport] = {}


class RoutingRepository:
    """Data access repository for document routing telemetry."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db

    def save_report(self, report: DocumentRoutingReport) -> None:
        """Persist routing report to database or memory cache."""
        _TELEMETRY_CACHE[report.document_id] = report

        if self.db is not None:
            doc = self.db.query(Document).filter(Document.id == report.document_id).first()
            if doc:
                # Store serialized metrics in document metadata dictionary
                current_meta = dict(doc.metadata_info or {})
                current_meta["routing_report"] = report.model_dump(mode="json")
                doc.metadata_info = current_meta
                self.db.add(doc)
                self.db.commit()
                logger.info(f"Persisted routing telemetry for document {report.document_id}")

    def get_report(self, document_id: str) -> Optional[DocumentRoutingReport]:
        """Retrieve routing report by document ID."""
        # Check in-memory cache first
        if document_id in _TELEMETRY_CACHE:
            return _TELEMETRY_CACHE[document_id]

        if self.db is not None:
            doc = self.db.query(Document).filter(Document.id == document_id).first()
            if doc and doc.metadata_info and "routing_report" in doc.metadata_info:
                data = doc.metadata_info["routing_report"]
                report = DocumentRoutingReport.model_validate(data)
                _TELEMETRY_CACHE[document_id] = report
                return report

        return None

    def clear_cache(self) -> None:
        """Utility for test isolation."""
        _TELEMETRY_CACHE.clear()
