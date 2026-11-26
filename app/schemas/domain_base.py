"""Base Domain Schemas and Common Reusable Value Objects.

Provides foundation models, address formats, monetary types, and entity structures
for typed document intelligence extraction.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class PostalAddress(BaseModel):
    """Structured physical or billing postal address."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    street: Optional[str] = Field(default=None, description="Street address including building or suite number.")
    city: Optional[str] = Field(default=None, description="City or municipality.")
    state: Optional[str] = Field(default=None, description="State, province, or region code.")
    postal_code: Optional[str] = Field(default=None, description="ZIP or postal routing code.")
    country: Optional[str] = Field(default=None, description="Two-letter ISO country code or full country name.")


class PartyEntity(BaseModel):
    """Business entity, vendor, customer, or institution appearing in a document."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    name: str = Field(..., description="Legal or trade name of the entity.")
    tax_id: Optional[str] = Field(default=None, description="VAT, GSTIN, EIN, or tax identification number.")
    email: Optional[str] = Field(default=None, description="Contact email address.")
    phone: Optional[str] = Field(default=None, description="Contact telephone or mobile number.")
    address: Optional[PostalAddress] = Field(default=None, description="Entity physical or registered address.")


class CurrencyAmount(BaseModel):
    """Monetary quantity with associated currency ISO code or symbol."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    amount: float = Field(..., description="Numerical monetary value.")
    currency: str = Field(default="USD", description="Currency ISO 4217 code (USD, EUR, GBP, INR).")


class BaseDocumentSchema(BaseModel):
    """Root model for all domain-specific document extraction schemas."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    schema_version: str = Field(default="1.0.0", description="SemVer version of the extraction schema.")
    doc_type: str = Field(..., description="Document domain category (e.g. invoice, receipt, medical_bill).")
    document_date: Optional[str] = Field(default=None, description="Primary document issue or transaction date (YYYY-MM-DD).")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Overall extraction model confidence.")
    notes: Optional[str] = Field(default=None, description="Auxiliary document notes or remarks.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary unmapped metadata fields.")
