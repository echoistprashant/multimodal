"""Multimodal Vision VLM Schemas and Contracts.

Defines image payloads, base64 data representations, and the Multimodal VLM protocol.
"""

from typing import List, Protocol, runtime_checkable
from pydantic import BaseModel, ConfigDict, Field

from app.extraction.prompt_schema import FormattedExtractionPrompt
from app.extraction.schema import LLMExtractionResult


class MultimodalPayload(BaseModel):
    """Payload bundling text prompt instructions with high-resolution page image frames."""

    model_config = ConfigDict(frozen=True)

    prompt: FormattedExtractionPrompt
    image_bytes_list: List[bytes] = Field(default_factory=list, description="Raw binary image data for document pages.")
    image_mime_types: List[str] = Field(default_factory=list, description="MIME types (e.g. 'image/png', 'image/jpeg').")
    dpi: int = Field(default=200, ge=72, le=600)


@runtime_checkable
class VLMExtractorProtocol(Protocol):
    """Protocol establishing common interface for multimodal vision-language extractors."""

    async def extract_multimodal(self, payload: MultimodalPayload) -> LLMExtractionResult:
        """Execute multimodal vision reasoning on prompt and image frames."""
        ...
