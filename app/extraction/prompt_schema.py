"""Extraction Prompt Engineering Schemas and Context Contracts.

Defines schemas for dynamic prompt assembly, few-shot examples,
and structured system/user prompt payloads.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ExtractionPromptContext(BaseModel):
    """Contextual parameters required to generate an extraction prompt for an LLM/VLM."""

    model_config = ConfigDict(frozen=True)

    doc_type: str = Field(..., description="Target document schema type (e.g. invoice, receipt).")
    document_text: str = Field(..., description="Markdown or text representation of document content.")
    json_schema: Dict[str, Any] = Field(..., description="Pydantic JSON schema specification for output formatting.")
    field_guidance: Optional[str] = Field(default=None, description="Detailed field-level rules and format hints.")
    few_shot_examples: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Optional curated input-output example pairs for few-shot in-context learning.",
    )


class FormattedExtractionPrompt(BaseModel):
    """Final rendered system and user prompt strings ready for dispatch to inference API."""

    model_config = ConfigDict(frozen=True)

    system_prompt: str = Field(..., description="System instructions establishing role, schema constraints, and rules.")
    user_prompt: str = Field(..., description="Delimited document content and extraction trigger.")
    target_schema_name: str = Field(..., description="Target schema name for auditing and logging.")
