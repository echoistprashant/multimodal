"""Unit tests for Phase 8 Part 8.1: Domain Pydantic Document Schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.domain_base import PartyEntity, PostalAddress
from app.schemas.invoice import InvoiceLineItem, InvoiceSchema, InvoiceTaxDetail
from app.schemas.receipt_medical import MedicalBillSchema, ReceiptSchema


def test_invoice_schema_validation() -> None:
    """Verify standard commercial invoice instantiates and validates correctly."""
    invoice_data = {
        "invoice_number": "INV-2026-9912",
        "document_date": "2026-11-20",
        "due_date": "2026-12-20",
        "vendor": {
            "name": "Global Tech Infrastructure LLC",
            "tax_id": "US-EIN-9928172",
            "email": "billing@globaltech.com",
            "address": {
                "street": "100 Innovation Way",
                "city": "Austin",
                "state": "TX",
                "postal_code": "78701",
                "country": "US",
            },
        },
        "customer": {
            "name": "Acme Ventures Inc",
        },
        "line_items": [
            {
                "description": "Dedicated Cloud Cluster Hosting",
                "quantity": 2.0,
                "unit_price": 500.0,
                "amount": 1000.0,
            },
            {
                "description": "Premium 24/7 SLA Support",
                "quantity": 1.0,
                "unit_price": 250.0,
                "amount": 250.0,
            },
        ],
        "subtotal": 1250.0,
        "tax_amount": 100.0,
        "tax_details": [
            {
                "tax_name": "State Sales Tax",
                "rate_percentage": 8.0,
                "amount": 100.0,
            }
        ],
        "total_amount": 1350.0,
        "currency": "USD",
    }

    inv = InvoiceSchema.model_validate(invoice_data)
    assert inv.invoice_number == "INV-2026-9912"
    assert inv.vendor.name == "Global Tech Infrastructure LLC"
    assert len(inv.line_items) == 2
    assert inv.total_amount == 1350.0
    assert inv.doc_type == "invoice"


def test_receipt_schema_validation() -> None:
    """Verify POS retail receipt model fields and defaults."""
    receipt = ReceiptSchema(
        merchant_name="Whole Foods Market",
        total_amount=48.75,
        tax_amount=3.25,
        payment_method="card",
        items=[
            InvoiceLineItem(description="Organic Almond Milk", amount=4.50),
            InvoiceLineItem(description="Avocado 4-pack", amount=5.99),
        ],
    )
    assert receipt.merchant_name == "Whole Foods Market"
    assert receipt.total_amount == 48.75
    assert len(receipt.items) == 2


def test_medical_bill_schema_validation() -> None:
    """Verify healthcare medical bill schema fields."""
    bill = MedicalBillSchema(
        patient_name="John Doe",
        hospital_name="St. Jude Memorial Hospital",
        admission_date="2026-10-01",
        discharge_date="2026-10-04",
        treatment_description="Appendectomy and Post-Op Care",
        total_billed_amount=15400.0,
        insurance_provider="BlueCross",
        insurance_claim_amount=13500.0,
        copay_amount=250.0,
        patient_responsibility_amount=1650.0,
    )
    assert bill.patient_name == "John Doe"
    assert bill.hospital_name == "St. Jude Memorial Hospital"
    assert bill.total_billed_amount == 15400.0


def test_missing_required_fields_raises_validation_error() -> None:
    """Verify omission of mandatory fields raises Pydantic ValidationError."""
    with pytest.raises(ValidationError):
        # Missing required vendor and total_amount
        InvoiceSchema.model_validate({"invoice_number": "INV-001"})
