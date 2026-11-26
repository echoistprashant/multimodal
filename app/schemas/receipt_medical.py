"""Schemas for Retail Receipts and Healthcare Medical Invoices.

Defines schemas with field validations, patient responsibility calculations,
and retail merchant receipt structures.
"""

from typing import List, Optional
from pydantic import ConfigDict, Field

from app.schemas.domain_base import BaseDocumentSchema, PostalAddress
from app.schemas.invoice import InvoiceLineItem


class ReceiptSchema(BaseDocumentSchema):
    """Schema for Point-of-Sale (POS), retail, hospitality, and fuel receipts."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    doc_type: str = Field(default="receipt")
    merchant_name: str = Field(..., description="Store or merchant brand name.")
    merchant_address: Optional[PostalAddress] = Field(default=None)
    merchant_phone: Optional[str] = Field(default=None)
    receipt_number: Optional[str] = Field(default=None, description="POS register slip or transaction sequence.")
    payment_method: Optional[str] = Field(
        default=None,
        description="Payment tender type: 'cash', 'card', 'upi', 'apple_pay', etc.",
    )
    subtotal: Optional[float] = Field(default=None, ge=0.0)
    tax_amount: Optional[float] = Field(default=0.0, ge=0.0)
    tip_amount: Optional[float] = Field(default=0.0, ge=0.0)
    total_amount: float = Field(..., ge=0.0, description="Grand total transaction amount charged.")
    currency: str = Field(default="USD")
    items: List[InvoiceLineItem] = Field(default_factory=list)


class MedicalBillSchema(BaseDocumentSchema):
    """Schema for hospital, clinical laboratory, and healthcare service bills."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    doc_type: str = Field(default="medical_bill")
    patient_name: str = Field(..., description="Full legal name of the patient.")
    patient_id: Optional[str] = Field(default=None, description="Medical Record Number (MRN) or Patient ID.")
    hospital_name: str = Field(..., description="Name of the hospital, clinic, or medical network.")
    attending_physician: Optional[str] = Field(default=None, description="Doctor or provider name.")
    admission_date: Optional[str] = Field(default=None, description="Inpatient admission date (YYYY-MM-DD).")
    discharge_date: Optional[str] = Field(default=None, description="Inpatient discharge date (YYYY-MM-DD).")
    treatment_description: Optional[str] = Field(default=None, description="Primary clinical diagnosis or procedure summary.")
    insurance_provider: Optional[str] = Field(default=None, description="Health insurance carrier / payer.")
    insurance_policy_number: Optional[str] = Field(default=None, description="Policy or member ID.")
    insurance_claim_amount: Optional[float] = Field(default=0.0, ge=0.0, description="Amount billed to insurance.")
    copay_amount: Optional[float] = Field(default=0.0, ge=0.0, description="Patient co-payment amount.")
    total_billed_amount: float = Field(..., ge=0.0, description="Total hospital charges.")
    patient_responsibility_amount: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Out-of-pocket amount due from patient.",
    )
    line_items: List[InvoiceLineItem] = Field(default_factory=list, description="Itemized clinical line charges.")
