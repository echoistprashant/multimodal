"""Field Guidance Metadata and Extraction Annotations.

Defines schemas detailing field-level extraction instructions, formatting constraints,
and anti-hallucination policies for LLM prompt engineering.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class FieldGuidance(BaseModel):
    """Extraction instruction metadata associated with an individual schema property."""

    model_config = ConfigDict(frozen=True)

    field_name: str = Field(..., description="Target schema property name.")
    data_type: str = Field(..., description="Python/JSON data type representation.")
    description: str = Field(..., description="Semantic purpose and extraction instructions for the field.")
    required: bool = Field(default=False, description="Whether field is strictly required or optional.")
    format_hint: Optional[str] = Field(default=None, description="Expected formatting (e.g., 'YYYY-MM-DD', 'ISO-4217').")
    synonyms: List[str] = Field(default_factory=list, description="Alternative textual labels commonly found in source documents.")
    null_if_absent: bool = Field(
        default=True,
        description="Policy instructing LLM to emit null if not explicitly found in document, preventing hallucinated defaults.",
    )
