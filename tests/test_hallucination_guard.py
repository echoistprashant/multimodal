"""Unit tests for Phase 10 Part 10.3: Hallucination Guard and Provenance Persistence."""

from app.grounding.hallucination_guard import HallucinationGuard
from app.grounding.schema import GroundedSpan, GroundingStatus, ProvenanceMatch
from app.repositories.extraction_repo import ExtractionRepository


def test_hallucination_guard_flags_critical_ungrounded() -> None:
    """Verify ungrounded critical fields trigger human review requirement."""
    matches = [
        ProvenanceMatch(
            field_path="invoice_number",
            extracted_value="INV-999",
            status=GroundingStatus.EXACT,
            grounded=True,
            confidence=1.0,
            best_span=GroundedSpan(page_no=1, bbox=(0.1, 0.1, 0.3, 0.15), source_text="INV-999", match_score=1.0),
        ),
        ProvenanceMatch(
            field_path="total_amount",
            extracted_value=9999.0,
            status=GroundingStatus.UNGROUNDED,
            grounded=False,
            confidence=0.0,
        ),
    ]

    guard = HallucinationGuard()
    report = guard.audit("doc-1", matches)
    assert report.grounded_count == 1
    assert report.ungrounded_count == 1
    assert "total_amount" in report.critical_ungrounded_fields
    assert report.hallucination_rate == 0.5
    assert report.requires_human_review is True


def test_extraction_repository_save_and_get() -> None:
    """Verify provenance matches persist and retrieve accurately."""
    repo = ExtractionRepository()
    repo.clear_cache()

    matches = [
        ProvenanceMatch(
            field_path="vendor.name",
            extracted_value="Acme Corp",
            status=GroundingStatus.EXACT,
            grounded=True,
            confidence=1.0,
            best_span=GroundedSpan(page_no=1, bbox=(0.1, 0.2, 0.4, 0.25), source_text="Acme Corp", match_score=1.0),
        )
    ]
    saved = repo.save_provenance_matches("doc-repo-1", matches)
    assert len(saved) == 1
    assert saved[0].bbox == [0.1, 0.2, 0.4, 0.25]

    loaded = repo.get_fields("doc-repo-1")
    assert len(loaded) == 1
    assert loaded[0].field_path == "vendor.name"
    assert loaded[0].grounded is True
