"""Repository for Persisting Extracted Fields and Provenance Records."""

from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.core.logging import get_logger
from app.grounding.schema import ProvenanceMatch

logger = get_logger("app.repositories.extraction_repo")


class StoredFieldRecord(BaseModel):
    """Serialized ExtractedField record with bounding-box provenance and validation state."""

    model_config = ConfigDict(frozen=False)

    field_id: str
    document_id: str
    field_path: str
    value: object
    confidence: float
    page_no: int = 1
    bbox: List[float] = Field(default_factory=list)
    source_text: str = ""
    grounded: bool = False
    validation_status: str = "unchecked"
    validation_messages: List[str] = Field(default_factory=list)
    review_status: str = "pending"


_EXTRACTED_FIELDS_CACHE: Dict[str, List[StoredFieldRecord]] = {}


class ExtractionRepository:
    """Data access layer for storing and retrieving grounded extracted fields."""

    def save_provenance_matches(
        self,
        document_id: str,
        matches: List[ProvenanceMatch],
    ) -> List[StoredFieldRecord]:
        """Persist provenance matches for a document."""
        records: List[StoredFieldRecord] = []
        for idx, m in enumerate(matches):
            span = m.best_span
            records.append(
                StoredFieldRecord(
                    field_id=f"{document_id}::field_{idx}",
                    document_id=document_id,
                    field_path=m.field_path,
                    value=m.extracted_value,
                    confidence=m.confidence,
                    page_no=span.page_no if span else 1,
                    bbox=list(span.bbox) if span else [],
                    source_text=span.source_text if span else "",
                    grounded=m.grounded,
                )
            )
        _EXTRACTED_FIELDS_CACHE[document_id] = records
        logger.info(f"Stored {len(records)} grounded field records for document {document_id}")
        return records

    def get_fields(self, document_id: str) -> List[StoredFieldRecord]:
        """Retrieve all stored field records for a document."""
        return list(_EXTRACTED_FIELDS_CACHE.get(document_id, []))

    def update_fields(self, document_id: str, records: List[StoredFieldRecord]) -> None:
        """Overwrite stored field records (e.g. after validation or human review)."""
        _EXTRACTED_FIELDS_CACHE[document_id] = records

    def clear_cache(self) -> None:
        """Clear in-memory store for test isolation."""
        _EXTRACTED_FIELDS_CACHE.clear()
