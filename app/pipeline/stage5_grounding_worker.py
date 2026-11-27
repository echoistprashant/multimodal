"""Stage 5 Pipeline Worker: Grounding, Provenance & Hallucination Audit."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.core.logging import get_logger
from app.grounding.audit_schema import HallucinationReport
from app.grounding.grounder import DocumentGrounder
from app.grounding.hallucination_guard import HallucinationGuard
from app.grounding.schema import ProvenanceMatch
from app.repositories.extraction_repo import ExtractionRepository
from app.tables.grid_schema import StructuredTable

logger = get_logger("app.pipeline.stage5_grounding_worker")


class Stage5GroundingResult(BaseModel):
    """Output of Stage 5 Grounding and Provenance pipeline stage."""

    model_config = ConfigDict(frozen=True)

    document_id: str
    matches: List[ProvenanceMatch] = Field(default_factory=list)
    audit_report: HallucinationReport


class Stage5GroundingWorker:
    """Worker grounding extracted payloads back to page tokens and auditing hallucinations."""

    def __init__(
        self,
        grounder: Optional[DocumentGrounder] = None,
        guard: Optional[HallucinationGuard] = None,
        repo: Optional[ExtractionRepository] = None,
    ) -> None:
        self.grounder = grounder or DocumentGrounder()
        self.guard = guard or HallucinationGuard()
        self.repo = repo or ExtractionRepository()

    def process_document(
        self,
        document_id: str,
        extracted_data: Dict[str, Any],
        pages_tokens: Dict[int, List[dict]],
        tables: Optional[List[StructuredTable]] = None,
    ) -> Stage5GroundingResult:
        """Ground extracted fields, audit hallucinations, and persist field provenance."""
        logger.info(f"Running Stage 5 Grounding Worker for document '{document_id}'")
        matches = self.grounder.ground_payload(extracted_data, pages_tokens, tables=tables)
        audit_report = self.guard.audit(document_id, matches)
        self.repo.save_provenance_matches(document_id, matches)

        return Stage5GroundingResult(
            document_id=document_id,
            matches=matches,
            audit_report=audit_report,
        )
