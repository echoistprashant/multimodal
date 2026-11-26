"""Unit tests for Phase 8 Part 8.2: Hybrid Document Type Classification."""

from app.classifier.hybrid_classifier import HybridDocumentClassifier
from app.classifier.schema import DocumentType


def test_classify_invoice() -> None:
    """Verify invoice text triggers invoice category classification."""
    text = (
        "ACME LOGISTICS CORP\n"
        "TAX INVOICE #99481\n"
        "Date: 2026-11-20\n"
        "Bill To: Global Distribution LLC\n"
        "Due Date: 2026-12-20\n"
        "Amount Due: $1,250.00\n"
    )
    classifier = HybridDocumentClassifier()
    res = classifier.classify_document(text)
    assert res.predicted_type == DocumentType.INVOICE
    assert res.confidence > 0.70
    assert any("invoice" in k for k in res.matched_keywords)


def test_classify_receipt() -> None:
    """Verify retail receipt text with tall paper aspect ratio triggers receipt category."""
    text = (
        "WALMART SUPERCENTER\n"
        "STORE #2819\n"
        "CASHIER: SARAH\n"
        "REGISTER #12\n"
        "SUBTOTAL: $34.12\n"
        "TAX: $2.50\n"
        "TOTAL: $36.62\n"
        "CHANGE DUE: $3.38\n"
        "VISA TENDER APPROVED\n"
    )
    classifier = HybridDocumentClassifier()
    res = classifier.classify_document(text, aspect_ratio=2.5)
    assert res.predicted_type == DocumentType.RECEIPT
    assert res.confidence > 0.70


def test_classify_medical_bill() -> None:
    """Verify hospital clinical invoice triggers medical bill classification."""
    text = (
        "MAYO CLINIC HEALTH SYSTEM\n"
        "PATIENT NAME: Robert Smith\n"
        "PATIENT ID: MRN-88192\n"
        "PHYSICIAN: Dr. Emily Watson MD\n"
        "ADMISSION DATE: 2026-09-15\n"
        "DISCHARGE DATE: 2026-09-18\n"
        "COPAYMENT RECEIVED: $150.00\n"
        "INSURANCE CLAIM SUBMITTED TO AETNA\n"
    )
    classifier = HybridDocumentClassifier()
    res = classifier.classify_document(text)
    assert res.predicted_type == DocumentType.MEDICAL_BILL
    assert res.confidence > 0.70


def test_classify_financial_report() -> None:
    """Verify balance sheet and financial statements classify as financial report."""
    text = (
        "ALPHABET INC. CONSOLIDATED STATEMENTS OF INCOME\n"
        "FISCAL YEAR ENDED DECEMBER 31, 2025\n"
        "BALANCE SHEET HIGHLIGHTS\n"
        "REVENUE AND OPERATING CASH FLOWS\n"
        "SHAREHOLDERS' EQUITY AND EBITDA RECONCILIATION\n"
    )
    classifier = HybridDocumentClassifier()
    res = classifier.classify_document(text)
    assert res.predicted_type == DocumentType.FINANCIAL_REPORT
    assert res.confidence > 0.70


def test_classify_unknown_gibberish() -> None:
    """Verify random text without diagnostic markers outputs UNKNOWN category."""
    text = "The quick brown fox jumps over the lazy dog repeatedly in an open field."
    classifier = HybridDocumentClassifier()
    res = classifier.classify_document(text)
    assert res.predicted_type == DocumentType.UNKNOWN
    assert res.confidence <= 0.60
