"""Straight-Through Processing (STP) Auto-Approval Gateway."""

from typing import List, Optional
from app.grounding.audit_schema import HallucinationReport
from app.review.gateway_schema import ApprovalDecision, GatewayVerdict, STPPolicy
from app.validation.confidence_schema import ConfidenceBreakdown
from app.validation.schema import ValidationResult


class STPGateway:
    """Evaluates validation, grounding, and confidence to decide auto-approval vs human review."""

    def __init__(self, policy: Optional[STPPolicy] = None) -> None:
        self.policy = policy or STPPolicy()

    def evaluate(
        self,
        document_id: str,
        confidence: ConfidenceBreakdown,
        validation: ValidationResult,
        hallucination_report: HallucinationReport,
    ) -> GatewayVerdict:
        """Determine whether document qualifies for Straight-Through Processing."""
        reasons: List[str] = []
        flagged = set()

        # 1. Check arithmetic and cross-field validation errors
        if self.policy.require_zero_validation_errors and not validation.is_valid:
            reasons.append(f"Document failed {validation.error_count} deterministic validation rule(s).")
            for v in validation.violations:
                flagged.add(v.field_path)

        # 2. Check critical ungrounded fields
        if self.policy.require_all_critical_grounded and hallucination_report.critical_ungrounded_fields:
            reasons.append(
                f"Critical fields ungrounded: {', '.join(hallucination_report.critical_ungrounded_fields)}."
            )
            flagged.update(hallucination_report.critical_ungrounded_fields)

        # 3. Check composite confidence threshold
        if confidence.calibrated_score < self.policy.min_composite_confidence:
            reasons.append(
                f"Composite confidence {confidence.calibrated_score:.2f} below STP threshold "
                f"{self.policy.min_composite_confidence:.2f}."
            )

        # 4. Check per-field confidence threshold
        low_fields = [
            fp for fp, sc in confidence.field_scores.items()
            if sc < self.policy.min_field_confidence
        ]
        if low_fields:
            reasons.append(f"Low confidence fields detected: {', '.join(low_fields)}.")
            flagged.update(low_fields)

        if not reasons:
            return GatewayVerdict(
                document_id=document_id,
                decision=ApprovalDecision.AUTO_APPROVED,
                composite_confidence=confidence.calibrated_score,
                reasons=["Passed all deterministic rules, grounding checks, and confidence thresholds."],
                flagged_fields=[],
            )

        return GatewayVerdict(
            document_id=document_id,
            decision=ApprovalDecision.NEEDS_REVIEW,
            composite_confidence=confidence.calibrated_score,
            reasons=reasons,
            flagged_fields=sorted(list(flagged)),
        )
