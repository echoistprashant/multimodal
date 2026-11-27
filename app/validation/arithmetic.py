"""Deterministic Arithmetic Validation Rules for Financial Documents.

Verifies mathematical integrity across line items, subtotals, tax amounts,
and grand totals with configurable rounding tolerance.
"""

from typing import Any, Dict, List
from app.validation.schema import RuleViolation, ValidationSeverity


def check_arithmetic_rules(
    data: Dict[str, Any],
    tolerance: float = 0.05,
) -> List[RuleViolation]:
    """Run deterministic arithmetic checks on invoice, receipt, or medical bill payloads."""
    violations: List[RuleViolation] = []

    # 1. Line-item quantity * unit_price == amount
    items = data.get("line_items") or data.get("items") or []
    line_sum = 0.0
    has_line_items = False

    if isinstance(items, list):
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            has_line_items = True
            amt = item.get("amount")
            qty = item.get("quantity")
            unit_p = item.get("unit_price")

            if isinstance(amt, (int, float)):
                line_sum += float(amt)
                if isinstance(qty, (int, float)) and isinstance(unit_p, (int, float)):
                    expected_amt = round(float(qty) * float(unit_p), 2)
                    if abs(float(amt) - expected_amt) > tolerance:
                        violations.append(
                            RuleViolation(
                                rule_id="ARITH_LINE_ITEM_MULTIPLY",
                                field_path=f"line_items[{idx}].amount",
                                severity=ValidationSeverity.ERROR,
                                message=(
                                    f"Line item {idx} amount ({amt}) does not match "
                                    f"quantity ({qty}) * unit_price ({unit_p}) = {expected_amt}."
                                ),
                                expected_value=expected_amt,
                                actual_value=amt,
                            )
                        )

    # 2. Sum of line items == subtotal
    subtotal = data.get("subtotal")
    if has_line_items and isinstance(subtotal, (int, float)):
        rounded_sum = round(line_sum, 2)
        if abs(float(subtotal) - rounded_sum) > tolerance:
            violations.append(
                RuleViolation(
                    rule_id="ARITH_SUBTOTAL_SUM",
                    field_path="subtotal",
                    severity=ValidationSeverity.ERROR,
                    message=f"Subtotal ({subtotal}) does not equal sum of line items ({rounded_sum}).",
                    expected_value=rounded_sum,
                    actual_value=subtotal,
                )
            )

    # 3. Subtotal + Tax + Tip == Total Amount
    total = data.get("total_amount")
    if total is None:
        total = data.get("total_billed_amount")
    tax = data.get("tax_amount") or 0.0
    tip = data.get("tip_amount") or 0.0

    if isinstance(subtotal, (int, float)) and isinstance(total, (int, float)) and isinstance(tax, (int, float)):
        expected_total = round(float(subtotal) + float(tax) + float(tip), 2)
        if abs(float(total) - expected_total) > tolerance:
            violations.append(
                RuleViolation(
                    rule_id="ARITH_GRAND_TOTAL_MATCH",
                    field_path="total_amount",
                    severity=ValidationSeverity.ERROR,
                    message=(
                        f"Total amount ({total}) does not equal subtotal ({subtotal}) + "
                        f"tax ({tax}) + tip ({tip}) = {expected_total}."
                    ),
                    expected_value=expected_total,
                    actual_value=total,
                )
            )

    return violations
