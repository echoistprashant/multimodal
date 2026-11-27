"""Composite Confidence Calculator Combining OCR, LLM, Grounding, and Rules."""

from typing import Dict, List, Optional
from app.grounding.schema import ProvenanceMatch
from app.validation.calibration import calibrate_confidence_score
from app.validation.confidence_schema import CalibrationWeights, ConfidenceBreakdown
from app.validation.schema import ValidationResult


def compute_composite_confidence(
    ocr_confidence: float,
    model_confidence: float,
    provenance_matches: List[ProvenanceMatch],
    validation_result: ValidationResult,
    weights: Optional[CalibrationWeights] = None,
    temperature: float = 1.0,
) -> ConfidenceBreakdown:
    """Calculate weighted composite and calibrated confidence scores."""
    w = weights or CalibrationWeights()

    # Grounding score = average grounding confidence across fields
    if provenance_matches:
        grounding_score = sum(m.confidence for m in provenance_matches) / len(provenance_matches)
    else:
        grounding_score = 0.0

    # Validation score: 1.0 if valid, penalized heavily per error
    if validation_result.is_valid:
        val_score = max(0.85, 1.0 - 0.05 * validation_result.warning_count)
    else:
        val_score = max(0.0, 0.5 - 0.20 * validation_result.error_count)

    total_w = w.ocr_weight + w.model_weight + w.grounding_weight + w.validation_weight
    raw_composite = (
        w.ocr_weight * ocr_confidence
        + w.model_weight * model_confidence
        + w.grounding_weight * grounding_score
        + w.validation_weight * val_score
    ) / max(total_w, 1e-6)

    raw_composite = round(max(0.0, min(1.0, raw_composite)), 4)
    calibrated = calibrate_confidence_score(raw_composite, temperature=temperature)

    # Per-field calibrated confidence
    violated_paths = {v.field_path for v in validation_result.violations}
    field_scores: Dict[str, float] = {}
    for m in provenance_matches:
        base_f = 0.5 * model_confidence + 0.5 * m.confidence
        if m.field_path in violated_paths:
            base_f *= 0.50
        field_scores[m.field_path] = round(max(0.0, min(1.0, base_f)), 4)

    return ConfidenceBreakdown(
        ocr_confidence=round(ocr_confidence, 4),
        model_confidence=round(model_confidence, 4),
        grounding_confidence=round(grounding_score, 4),
        validation_score=round(val_score, 4),
        raw_composite_score=raw_composite,
        calibrated_score=calibrated,
        field_scores=field_scores,
    )
