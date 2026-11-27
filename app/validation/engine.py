"""Extensible Deterministic Validation Rule Engine."""

from typing import Any, Dict, List
from app.validation.arithmetic import check_arithmetic_rules
from app.validation.cross_field import check_cross_field_rules
from app.validation.schema import RuleViolation, ValidationResult, ValidationSeverity


class ValidationRuleEngine:
    """Executes arithmetic and cross-field deterministic validators on extracted payloads."""

    def __init__(self, arithmetic_tolerance: float = 0.05) -> None:
        self.arithmetic_tolerance = arithmetic_tolerance

    def validate(self, extracted_data: Dict[str, Any]) -> ValidationResult:
        """Run all registered validation rule sets and return structured ValidationResult."""
        violations: List[RuleViolation] = []
        violations.extend(check_arithmetic_rules(extracted_data, tolerance=self.arithmetic_tolerance))
        violations.extend(check_cross_field_rules(extracted_data))

        error_count = sum(1 for v in violations if v.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for v in violations if v.severity == ValidationSeverity.WARNING)

        return ValidationResult(
            is_valid=(error_count == 0),
            rules_executed=6,
            violations=violations,
            error_count=error_count,
            warning_count=warning_count,
        )
