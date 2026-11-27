"""Validation Rule Engine Data Contracts and Schemas."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ValidationSeverity(str, Enum):
    """Severity level of a deterministic business rule violation."""

    ERROR = "error"      # Critical mismatch blocking auto-approval
    WARNING = "warning"  # Non-blocking anomaly logged for audit
    INFO = "info"


class RuleViolation(BaseModel):
    """Details of a single failed deterministic validation rule."""

    model_config = ConfigDict(frozen=True)

    rule_id: str = Field(..., description="Unique rule identifier (e.g. 'ARITH_SUBTOTAL_MATCH').")
    field_path: str = Field(..., description="Affected field path (e.g. 'total_amount', 'due_date').")
    severity: ValidationSeverity = Field(default=ValidationSeverity.ERROR)
    message: str = Field(..., description="Human-readable explanation of the discrepancy.")
    expected_value: Optional[object] = Field(default=None)
    actual_value: Optional[object] = Field(default=None)


class ValidationResult(BaseModel):
    """Aggregate result from running all deterministic validation rules on a document."""

    model_config = ConfigDict(frozen=True)

    is_valid: bool = Field(..., description="True if zero ERROR-severity violations occurred.")
    rules_executed: int = Field(ge=0)
    violations: List[RuleViolation] = Field(default_factory=list)
    error_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
