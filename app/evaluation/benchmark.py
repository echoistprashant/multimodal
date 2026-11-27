"""Structured Extraction Precision, Recall, F1, and Hallucination Evaluator."""

from typing import Any, Dict, List
from app.evaluation.extraction_metrics import FieldAccuracyMetrics, GroundingMetrics
from app.grounding.matcher import compute_fuzzy_similarity
from app.grounding.schema import ProvenanceMatch


def _flatten(d: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in d.items():
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_flatten(v, path))
        elif isinstance(v, list):
            for idx, item in enumerate(v):
                if isinstance(item, dict):
                    out.update(_flatten(item, f"{path}[{idx}]"))
                else:
                    out[f"{path}[{idx}]"] = item
        elif v is not None:
            out[path] = v
    return out


def evaluate_extraction_accuracy(
    predicted: Dict[str, Any],
    ground_truth: Dict[str, Any],
    fuzzy_threshold: float = 0.85,
) -> FieldAccuracyMetrics:
    """Compare predicted JSON payload against golden ground truth."""
    pred_flat = _flatten(predicted)
    gt_flat = _flatten(ground_truth)

    if not gt_flat and not pred_flat:
        return FieldAccuracyMetrics(
            exact_match_rate=1.0, fuzzy_match_rate=1.0, precision=1.0, recall=1.0, f1_score=1.0
        )
    if not gt_flat or not pred_flat:
        return FieldAccuracyMetrics(
            exact_match_rate=0.0, fuzzy_match_rate=0.0, precision=0.0, recall=0.0, f1_score=0.0
        )

    exact_hits = 0
    fuzzy_hits = 0

    for path, gt_val in gt_flat.items():
        if path not in pred_flat:
            continue
        p_val = pred_flat[path]
        if str(p_val).strip().lower() == str(gt_val).strip().lower():
            exact_hits += 1
            fuzzy_hits += 1
        elif compute_fuzzy_similarity(str(p_val), str(gt_val)) >= fuzzy_threshold:
            fuzzy_hits += 1

    precision = round(fuzzy_hits / len(pred_flat), 4)
    recall = round(fuzzy_hits / len(gt_flat), 4)
    f1 = round((2 * precision * recall) / (precision + recall), 4) if (precision + recall) > 0 else 0.0

    return FieldAccuracyMetrics(
        exact_match_rate=round(exact_hits / len(gt_flat), 4),
        fuzzy_match_rate=recall,
        precision=precision,
        recall=recall,
        f1_score=f1,
    )


def evaluate_grounding_metrics(matches: List[ProvenanceMatch]) -> GroundingMetrics:
    """Compute grounding coverage and hallucination rate from ProvenanceMatch list."""
    if not matches:
        return GroundingMetrics(grounding_coverage=1.0, hallucination_rate=0.0)
    grounded = sum(1 for m in matches if m.grounded)
    cov = round(grounded / len(matches), 4)
    return GroundingMetrics(grounding_coverage=cov, hallucination_rate=round(1.0 - cov, 4))
