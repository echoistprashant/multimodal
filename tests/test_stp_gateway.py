"""Unit tests for Phase 11 Part 11.3: STP Auto-Approval Gateway and Review Task Generation."""

from app.grounding.audit_schema import HallucinationReport
from app.grounding.schema import GroundedSpan, GroundingStatus, ProvenanceMatch
from app.pipeline.stage6_validation_worker import Stage6ValidationWorker
from app.repositories.extraction_repo import ExtractionRepository
from app.repositories.review_repo import ReviewQueueRepository
from app.review.gateway_schema import ApprovalDecision


def test_stp_auto_approved_document() -> None:
    """Verify clean, grounded, mathematically valid document is auto-approved."""
    ExtractionRepository().clear_cache()
    ReviewQueueRepository().clear_cache()

    matches = [
        ProvenanceMatch(
            field_path="total_amount",
            extracted_value=110.0,
            status=GroundingStatus.NUMERIC,
            grounded=True,
            confidence=1.0,
            best_span=GroundedSpan(page_no=1, bbox=(0.7, 0.7, 0.9, 0.75), source_text="$110.00", match_score=1.0),
        )
    ]
    ExtractionRepository().save_provenance_matches("doc-stp-pass", matches)
    audit = HallucinationReport(
        document_id="doc-stp-pass",
        total_fields_checked=1,
        grounded_count=1,
        ungrounded_count=0,
        hallucination_rate=0.0,
    )

    data = {"subtotal": 100.0, "tax_amount": 10.0, "total_amount": 110.0}
    res = Stage6ValidationWorker().process_document("doc-stp-pass", data, matches, audit)
    assert res.verdict.decision == ApprovalDecision.AUTO_APPROVED
    assert len(res.created_review_tasks) == 0


def test_stp_routes_violation_to_review_queue() -> None:
    """Verify arithmetic violation routes document to NEEDS_REVIEW and creates ReviewTask."""
    ExtractionRepository().clear_cache()
    ReviewQueueRepository().clear_cache()

    matches = [
        ProvenanceMatch(
            field_path="total_amount",
            extracted_value=999.0,
            status=GroundingStatus.UNGROUNDED,
            grounded=False,
            confidence=0.0,
        )
    ]
    ExtractionRepository().save_provenance_matches("doc-stp-fail", matches)
    audit = HallucinationReport(
        document_id="doc-stp-fail",
        total_fields_checked=1,
        grounded_count=0,
        ungrounded_count=1,
        ungrounded_fields=["total_amount"],
        critical_ungrounded_fields=["total_amount"],
        hallucination_rate=1.0,
        requires_human_review=True,
    )

    data = {"subtotal": 100.0, "tax_amount": 10.0, "total_amount": 999.0}
    res = Stage6ValidationWorker().process_document("doc-stp-fail", data, matches, audit)
    assert res.verdict.decision == ApprovalDecision.NEEDS_REVIEW
    assert len(res.created_review_tasks) == 1
    assert res.created_review_tasks[0].field_path == "total_amount"
