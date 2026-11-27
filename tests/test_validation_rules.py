"""Unit tests for Phase 11 Part 11.1: Arithmetic and Cross-Field Validation Engine."""

from app.validation.engine import ValidationRuleEngine


def test_valid_invoice_passes_all_rules() -> None:
    """Verify mathematically and chronologically consistent invoice passes cleanly."""
    payload = {
        "document_date": "2026-11-01",
        "due_date": "2026-12-01",
        "currency": "USD",
        "line_items": [
            {"description": "Node A", "quantity": 2.0, "unit_price": 250.0, "amount": 500.0},
            {"description": "Node B", "quantity": 1.0, "unit_price": 300.0, "amount": 300.0},
        ],
        "subtotal": 800.0,
        "tax_amount": 80.0,
        "total_amount": 880.0,
    }
    res = ValidationRuleEngine().validate(payload)
    assert res.is_valid is True
    assert res.error_count == 0


def test_arithmetic_mismatches_detected() -> None:
    """Verify line item math, subtotal sum, and grand total mismatches are flagged."""
    bad_payload = {
        "document_date": "2026-11-15",
        "due_date": "2026-11-01",  # Due before issue!
        "line_items": [
            {"description": "Item 1", "quantity": 2.0, "unit_price": 100.0, "amount": 250.0},  # 2*100 != 250
        ],
        "subtotal": 200.0,  # 250 != 200
        "tax_amount": 20.0,
        "total_amount": 999.0,  # 200+20 != 999
    }
    res = ValidationRuleEngine().validate(bad_payload)
    assert res.is_valid is False
    assert res.error_count == 4
    rule_ids = {v.rule_id for v in res.violations}
    assert "ARITH_LINE_ITEM_MULTIPLY" in rule_ids
    assert "ARITH_SUBTOTAL_SUM" in rule_ids
    assert "ARITH_GRAND_TOTAL_MATCH" in rule_ids
    assert "CROSS_DUE_BEFORE_ISSUE" in rule_ids
