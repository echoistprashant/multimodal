"""Extraction Engine Protocol and LLM Result Schemas.

Defines abstract extraction protocols, token utilization metrics,
and response containers for text LLMs and multimodal vision extractors.
"""

from typing import Any, Dict, Optional, Protocol, runtime_checkable
from pydantic import BaseModel, ConfigDict, Field

from app.extraction.prompt_schema import FormattedExtractionPrompt


class LLMExtractionResult(BaseModel):
    """Result returned by an LLM or VLM extraction invocation."""

    model_config = ConfigDict(frozen=True)

    raw_response: str = Field(..., description="Raw string content returned by the inference model.")
    parsed_json: Dict[str, Any] = Field(default_factory=dict, description="Parsed and validated JSON dictionary.")
    model_name: str = Field(..., description="Name or identifier of the inference model used.")
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    latency_ms: float = Field(default=0.0, ge=0.0)
    success: bool = Field(default=True)
    error_message: Optional[str] = Field(default=None)


@runtime_checkable
class ExtractorProtocol(Protocol):
    """Protocol establishing common interface for all text and multimodal extractors."""

    async def extract(self, prompt: FormattedExtractionPrompt) -> LLMExtractionResult:
        """Execute extraction inference and return structured LLMExtractionResult."""
        ...
