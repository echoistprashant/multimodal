"""Document Classification Data Contracts and Enums.

Defines document category classifications, feature score representations,
and classifier result schemas.
"""

from enum import Enum
from typing import Dict, List
from pydantic import BaseModel, ConfigDict, Field


class DocumentType(str, Enum):
    """Supported domain classification categories."""

    INVOICE = "invoice"
    RECEIPT = "receipt"
    MEDICAL_BILL = "medical_bill"
    FINANCIAL_REPORT = "financial_report"
    UNKNOWN = "unknown"


class ClassificationResult(BaseModel):
    """Categorical classification verdict with confidence and grounding feature scores."""

    model_config = ConfigDict(frozen=True)

    predicted_type: DocumentType = Field(..., description="Inferred document category.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence score.")
    matched_keywords: List[str] = Field(default_factory=list, description="Diagnostic keywords matched in text.")
    feature_scores: Dict[str, float] = Field(default_factory=dict, description="Relative scores across candidate classes.")
    explanation: str = Field(default="", description="Human-readable rationale for the classification decision.")
