"""Hallucination Guard and Ungrounded Field Detector.

Audits ProvenanceMatch lists to detect ungrounded extractions, compute document
hallucination rates, and flag critical fields for human-in-the-loop review.
"""

from typing import List, Optional
from app.grounding.audit_schema import GroundingAuditPolicy, HallucinationReport
from app.grounding.schema import ProvenanceMatch


class HallucinationGuard:
    """Evaluates grounding coverage and flags potential LLM hallucinations."""

    def __init__(self, policy: Optional[GroundingAuditPolicy] = None) -> None:
        self.policy = policy or GroundingAuditPolicy()

    def audit(self, document_id: str, matches: List[ProvenanceMatch]) -> HallucinationReport:
        """Analyze provenance matches and generate a HallucinationReport."""
        total = len(matches)
        if total == 0:
            return HallucinationReport(
                document_id=document_id,
                total_fields_checked=0,
                grounded_count=0,
                ungrounded_count=0,
                hallucination_rate=0.0,
                requires_human_review=False,
            )

        grounded_count = sum(1 for m in matches if m.grounded)
        ungrounded_fields = [m.field_path for m in matches if not m.grounded]
        ungrounded_count = len(ungrounded_fields)

        critical_ungrounded = [
            fp for fp in ungrounded_fields
            if any(fp == cf or fp.endswith(f".{cf}") for cf in self.policy.critical_fields)
        ]

        hallucination_rate = round(ungrounded_count / total, 4)
        requires_review = (
            len(critical_ungrounded) > 0
            or hallucination_rate > self.policy.max_allowed_ungrounded_ratio
        )

        return HallucinationReport(
            document_id=document_id,
            total_fields_checked=total,
            grounded_count=grounded_count,
            ungrounded_count=ungrounded_count,
            ungrounded_fields=ungrounded_fields,
            critical_ungrounded_fields=critical_ungrounded,
            hallucination_rate=hallucination_rate,
            requires_human_review=requires_review,
        )
