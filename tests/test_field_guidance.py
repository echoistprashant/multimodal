"""Unit tests for Phase 8 Part 8.4: Field Guidance and Anti-Hallucination Normalization."""

from app.schemas.guidance_generator import format_guidance_for_prompt, generate_schema_guidance
from app.schemas.invoice import InvoiceSchema
from app.schemas.validation_rules import (
    clean_extracted_value,
    coerce_monetary_value,
    sanitize_extraction_payload,
)


def test_schema_guidance_generation() -> None:
    """Verify guidance generator extracts field annotations, hints, and requirements."""
    guidance = generate_schema_guidance(InvoiceSchema)
    fields = {g.field_name: g for g in guidance}

    assert "invoice_number" in fields
    assert fields["invoice_number"].required is True
    assert "inv no" in fields["invoice_number"].synonyms

    assert "document_date" in fields
    assert fields["document_date"].format_hint is not None
    assert "YYYY-MM-DD" in fields["document_date"].format_hint

    assert "total_amount" in fields
    assert fields["total_amount"].required is True
    assert "Numeric decimal" in fields["total_amount"].format_hint


def test_format_guidance_prompt_string() -> None:
    """Verify guidance rules format into prompt-ready markdown string."""
    guidance = generate_schema_guidance(InvoiceSchema)
    prompt_str = format_guidance_for_prompt(guidance)
    assert "STRICT POLICY" in prompt_str
    assert "NEVER hallucinate" in prompt_str
    assert "**invoice_number** (REQUIRED)" in prompt_str


def test_clean_null_equivalent_values() -> None:
    """Verify placeholder string tokens are converted to None."""
    assert clean_extracted_value("N/A") is None
    assert clean_extracted_value("  none  ") is None
    assert clean_extracted_value("-") is None
    assert clean_extracted_value("not provided") is None
    assert clean_extracted_value("Valid Organization LLC") == "Valid Organization LLC"

    # Nested dictionary / list cleaning
    nested = {
        "name": "Acme",
        "po_number": "N/A",
        "items": ["Item A", "None", "-"],
    }
    cleaned = clean_extracted_value(nested)
    assert cleaned["po_number"] is None
    assert cleaned["items"] == ["Item A", None, None]


def test_coerce_monetary_values() -> None:
    """Verify currency symbols and thousands separators are stripped into float values."""
    assert coerce_monetary_value("$1,250.75") == 1250.75
    assert coerce_monetary_value("€ 99.00") == 99.00
    assert coerce_monetary_value("₹ 5,000") == 5000.0
    assert coerce_monetary_value(145.20) == 145.20
    assert coerce_monetary_value("N/A") is None


def test_sanitize_extraction_payload() -> None:
    """Verify end-to-end payload sanitization."""
    raw = {
        "invoice_number": "INV-101",
        "po_number": "N/A",
        "total_amount": "$1,450.00",
        "tax_amount": "None",
        "notes": "Payment via Wire",
    }
    sanitized = sanitize_extraction_payload(raw)
    assert sanitized["invoice_number"] == "INV-101"
    assert sanitized["po_number"] is None
    assert sanitized["total_amount"] == 1450.00
    assert sanitized["tax_amount"] is None
    assert sanitized["notes"] == "Payment via Wire"
