"""Unit tests for Phase 11 Part 11.2: Composite Confidence Scoring and Calibration."""

from app.grounding.schema import GroundedSpan, GroundingStatus, ProvenanceMatch
from app.validation.calibration import calibrate_confidence_score
from app.validation.confidence import compute_composite_confidence
from app.validation.schema import RuleViolation, ValidationResult, ValidationSeverity


def test_temperature_calibration() -> None:
    """Verify temperature > 1 softens extreme confidence and < 1 sharpens."""
    raw = 0.90
    softened = calibrate_confidence_score(raw, temperature=1.5)
    sharpened = calibrate_confidence_score(raw, temperature=0.5)
    assert softened < raw
    assert sharpened > raw


def test_composite_confidence_high_vs_penalized() -> None:
    """Verify valid grounded document achieves high score while violation drops it."""
    matches = [
        ProvenanceMatch(
            field_path="total_amount",
            extracted_value=500.0,
            status=GroundingStatus.NUMERIC,
            grounded=True,
            confidence=1.0,
            best_span=GroundedSpan(page_no=1, bbox=(0.7, 0.8, 0.9, 0.85), source_text="$500.00", match_score=1.0),
        )
    ]
    valid_res = ValidationResult(is_valid=True, rules_executed=5, error_count=0, warning_count=0)
    high_bd = compute_composite_confidence(0.95, 0.92, matches, valid_res)
    assert high_bd.calibrated_score > 0.90
    assert high_bd.field_scores["total_amount"] > 0.90

    invalid_res = ValidationResult(
        is_valid=False,
        rules_executed=5,
        error_count=2,
        warning_count=0,
        violations=[
            RuleViolation(
                rule_id="ARITH_GRAND_TOTAL_MATCH",
                field_path="total_amount",
                severity=ValidationSeverity.ERROR,
                message="Mismatch",
            )
        ],
    )
    low_bd = compute_composite_confidence(0.95, 0.92, matches, invalid_res)
    assert low_bd.calibrated_score < high_bd.calibrated_score
    assert low_bd.field_scores["total_amount"] < 0.55
