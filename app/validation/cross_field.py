"""Cross-Field Chronological and Domain Consistency Rules."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from app.validation.schema import RuleViolation, ValidationSeverity

VALID_ISO_CURRENCIES = {"USD", "EUR", "GBP", "INR", "CAD", "AUD", "JPY"}


def _parse_iso(date_val: Any) -> Optional[datetime]:
    if not isinstance(date_val, str) or not date_val.strip():
        return None
    try:
        return datetime.strptime(date_val.strip()[:10], "%Y-%m-%d")
    except ValueError:
        return None


def check_cross_field_rules(data: Dict[str, Any]) -> List[RuleViolation]:
    """Validate chronological date order and ISO currency code integrity."""
    violations: List[RuleViolation] = []

    # 1. Invoice: due_date >= document_date
    doc_dt = _parse_iso(data.get("document_date"))
    due_dt = _parse_iso(data.get("due_date"))
    if doc_dt and due_dt and due_dt < doc_dt:
        violations.append(
            RuleViolation(
                rule_id="CROSS_DUE_BEFORE_ISSUE",
                field_path="due_date",
                severity=ValidationSeverity.ERROR,
                message=f"Due date ({data.get('due_date')}) cannot precede document date ({data.get('document_date')}).",
                expected_value=f">= {data.get('document_date')}",
                actual_value=data.get("due_date"),
            )
        )

    # 2. Medical Bill: discharge_date >= admission_date
    adm_dt = _parse_iso(data.get("admission_date"))
    dis_dt = _parse_iso(data.get("discharge_date"))
    if adm_dt and dis_dt and dis_dt < adm_dt:
        violations.append(
            RuleViolation(
                rule_id="CROSS_DISCHARGE_BEFORE_ADMISSION",
                field_path="discharge_date",
                severity=ValidationSeverity.ERROR,
                message=f"Discharge date ({data.get('discharge_date')}) precedes admission date ({data.get('admission_date')}).",
                expected_value=f">= {data.get('admission_date')}",
                actual_value=data.get("discharge_date"),
            )
        )

    # 3. Currency ISO validation
    currency = data.get("currency")
    if isinstance(currency, str) and currency.strip():
        norm_curr = currency.strip().upper()
        if norm_curr not in VALID_ISO_CURRENCIES:
            violations.append(
                RuleViolation(
                    rule_id="DOMAIN_UNKNOWN_CURRENCY",
                    field_path="currency",
                    severity=ValidationSeverity.WARNING,
                    message=f"Unrecognized currency code '{currency}'. Expected ISO-4217 code.",
                    actual_value=currency,
                )
            )

    return violations
