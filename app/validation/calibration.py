"""Confidence Score Calibration Utilities (Temperature & Platt Scaling)."""

import math


def calibrate_confidence_score(
    raw_score: float,
    temperature: float = 1.0,
    shift_bias: float = 0.0,
) -> float:
    """Apply logit temperature scaling to prevent overconfident probability predictions.

    Args:
        raw_score: Raw score in [0.0, 1.0].
        temperature: Temperature > 1.0 softens extreme confidences; < 1.0 sharpens.
        shift_bias: Optional Platt-style calibration bias offset.
    """
    if temperature <= 0:
        raise ValueError("Calibration temperature must be positive.")

    # Fast identity path when uncalibrated
    if temperature == 1.0 and shift_bias == 0.0:
        return round(max(0.0, min(1.0, raw_score)), 4)

    # Clamp away from 0/1 singularities before logit transform
    eps = 1e-5
    p = max(eps, min(1.0 - eps, raw_score))
    logit = math.log(p / (1.0 - p))
    scaled_logit = (logit / temperature) + shift_bias
    calibrated = 1.0 / (1.0 + math.exp(-scaled_logit))
    return round(calibrated, 4)
