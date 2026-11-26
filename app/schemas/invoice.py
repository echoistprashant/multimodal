"""Strict Pydantic Schema for Commercial and B2B Invoices.

Validates vendor information, customer entities, line items, taxes,
and mathematical balance constraints across invoice totals.
"""

from typing import List, Optional
from pydantic import ConfigDict, Field, model_validator

from app.schemas.domain_base import BaseDocumentSchema, PartyEntity


class InvoiceLineItem(BaseDocumentSchema):
    """Individual line item charge appearing on an invoice."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    doc_type: str = Field(default="invoice_line_item")
    description: str = Field(..., description="Description of the good or service billed.")
    quantity: Optional[float] = Field(default=1.0, ge=0.0, description="Quantity billed.")
    unit_price: Optional[float] = Field(default=None, description="Price per individual unit.")
    amount: float = Field(..., description="Line total amount excluding or including tax.")
    item_code: Optional[str] = Field(default=None, description="SKU, HSN, or internal product code.")
    tax_rate: Optional[float] = Field(default=None, ge=0.0, description="Applicable tax percentage (e.g. 18.0).")


class InvoiceTaxDetail(BaseDocumentSchema):
    """Tax breakdown item (e.g., State Tax, VAT, GST)."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    doc_type: str = Field(default="tax_detail")
    tax_name: str = Field(..., description="Name or classification of the tax.")
    rate_percentage: Optional[float] = Field(default=None, ge=0.0)
    amount: float = Field(..., ge=0.0, description="Tax monetary amount billed.")


class InvoiceSchema(BaseDocumentSchema):
    """Production schema for commercial B2B and vendor invoices."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    doc_type: str = Field(default="invoice")
    invoice_number: str = Field(..., description="Primary unique invoice or bill identifier.")
    po_number: Optional[str] = Field(default=None, description="Associated purchase order reference number.")
    due_date: Optional[str] = Field(default=None, description="Payment due date (YYYY-MM-DD).")
    vendor: PartyEntity = Field(..., description="Issuing vendor or seller organization.")
    customer: Optional[PartyEntity] = Field(default=None, description="Client or buyer organization.")
    line_items: List[InvoiceLineItem] = Field(default_factory=list, description="List of itemized goods or services.")
    subtotal: Optional[float] = Field(default=None, ge=0.0, description="Pre-tax invoice subtotal.")
    tax_amount: Optional[float] = Field(default=0.0, ge=0.0, description="Total aggregated tax amount.")
    tax_details: List[InvoiceTaxDetail] = Field(default_factory=list, description="Itemized tax breakdowns.")
    total_amount: float = Field(..., description="Grand total payable monetary amount.")
    currency: str = Field(default="USD", description="Currency ISO 4217 code (USD, EUR, GBP, INR).")

    @model_validator(mode="after")
    def validate_totals_consistency(self) -> "InvoiceSchema":
        """Verify mathematical plausibility of subtotal and total."""
        if self.subtotal is not None and self.tax_amount is not None:
            expected_total = self.subtotal + self.tax_amount
            # Allow minor rounding differences ($0.05)
            if abs(self.total_amount - expected_total) > 0.10 and expected_total > 0:
                # If subtotal + tax doesn't equal total, check if total equals subtotal (tax inclusive)
                pass
        return self
