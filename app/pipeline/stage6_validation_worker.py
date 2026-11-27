"""Stage 6 Pipeline Worker: Deterministic Validation & STP Auto-Approval Gateway."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.core.logging import get_logger
from app.grounding.audit_schema import HallucinationReport
from app.grounding.schema import ProvenanceMatch
from app.repositories.extraction_repo import ExtractionRepository
from app.repositories.review_repo import ReviewQueueRepository
from app.review.gateway_schema import GatewayVerdict
from app.review.stp_gateway import STPGateway
from app.review.task_generator import ReviewTaskItem, generate_review_tasks
from app.validation.confidence import compute_composite_confidence
from app.validation.confidence_schema import ConfidenceBreakdown
from app.validation.engine import ValidationRuleEngine
from app.validation.schema import ValidationResult

logger = get_logger("app.pipeline.stage6_validation_worker")


class Stage6ValidationResult(BaseModel):
    """Complete output of Stage 6 Validation, Confidence Scoring, and STP Routing."""

    model_config = ConfigDict(frozen=True)

    document_id: str
    validation: ValidationResult
    confidence: ConfidenceBreakdown
    verdict: GatewayVerdict
    created_review_tasks: List[ReviewTaskItem] = Field(default_factory=list)


class Stage6ValidationWorker:
    """Orchestrates deterministic rules, confidence calibration, and HITL queue generation."""

    def __init__(
        self,
        rule_engine: Optional[ValidationRuleEngine] = None,
        gateway: Optional[STPGateway] = None,
        extraction_repo: Optional[ExtractionRepository] = None,
        review_repo: Optional[ReviewQueueRepository] = None,
    ) -> None:
        self.rule_engine = rule_engine or ValidationRuleEngine()
        self.gateway = gateway or STPGateway()
        self.extraction_repo = extraction_repo or ExtractionRepository()
        self.review_repo = review_repo or ReviewQueueRepository()

    def process_document(
        self,
        document_id: str,
        extracted_data: Dict[str, Any],
        provenance_matches: List[ProvenanceMatch],
        hallucination_report: HallucinationReport,
        ocr_confidence: float = 0.95,
        model_confidence: float = 0.92,
    ) -> Stage6ValidationResult:
        """Validate extracted data, compute confidence, and route to STP or review queue."""
        logger.info(f"Running Stage 6 Validation & STP Worker for document '{document_id}'")

        validation = self.rule_engine.validate(extracted_data)
        confidence = compute_composite_confidence(
            ocr_confidence=ocr_confidence,
            model_confidence=model_confidence,
            provenance_matches=provenance_matches,
            validation_result=validation,
        )
        verdict = self.gateway.evaluate(
            document_id=document_id,
            confidence=confidence,
            validation=validation,
            hallucination_report=hallucination_report,
        )

        stored_fields = self.extraction_repo.get_fields(document_id)
        review_tasks = generate_review_tasks(verdict, stored_fields)
        if review_tasks:
            self.review_repo.enqueue_tasks(review_tasks)

        return Stage6ValidationResult(
            document_id=document_id,
            validation=validation,
            confidence=confidence,
            verdict=verdict,
            created_review_tasks=review_tasks,
        )
