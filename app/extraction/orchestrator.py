"""Hybrid Extraction Orchestrator.

Coordinates cost-effective text LLM extraction with dynamic escalation to multimodal
vision models when documents present complex tabular layouts or text parsing fails.
"""

from typing import List, Optional, Type
from pydantic import BaseModel, ValidationError

from app.core.logging import get_logger
from app.extraction.prompt_schema import FormattedExtractionPrompt
from app.extraction.schema import ExtractorProtocol, LLMExtractionResult
from app.extraction.text_llm import TextLLMExtractor
from app.extraction.vlm_extractor import MultimodalVLMExtractor
from app.extraction.vlm_schema import MultimodalPayload, VLMExtractorProtocol
from app.routing.schema import RouteType

logger = get_logger("app.extraction.orchestrator")


class HybridExtractionOrchestrator:
    """Intelligent orchestrator executing text-first extraction with VLM vision fallback."""

    def __init__(
        self,
        text_extractor: Optional[ExtractorProtocol] = None,
        vlm_extractor: Optional[VLMExtractorProtocol] = None,
    ) -> None:
        self.text_extractor = text_extractor or TextLLMExtractor()
        self.vlm_extractor = vlm_extractor or MultimodalVLMExtractor()

    async def extract_document(
        self,
        prompt: FormattedExtractionPrompt,
        route: RouteType = RouteType.NATIVE,
        image_bytes_list: Optional[List[bytes]] = None,
        target_schema_cls: Optional[Type[BaseModel]] = None,
    ) -> LLMExtractionResult:
        """Route and execute extraction across Text or Multimodal pathways with auto-fallback."""
        # 1. Direct Multimodal VLM Route
        if route == RouteType.VLM:
            logger.info("Directly routing to Multimodal VLM based on triage recommendation.")
            payload = MultimodalPayload(
                prompt=prompt,
                image_bytes_list=image_bytes_list or [],
            )
            return await self.vlm_extractor.extract_multimodal(payload)

        # 2. Text-First Extraction Pathway (Native or OCR)
        logger.info(f"Attempting text-based extraction via pathway '{route.value}'.")
        text_result = await self.text_extractor.extract(prompt)

        # If text extraction succeeded and schema validation passes, accept result
        if text_result.success and text_result.parsed_json:
            if target_schema_cls is not None:
                try:
                    target_schema_cls.model_validate(text_result.parsed_json)
                    return text_result
                except ValidationError as val_err:
                    logger.warning(f"Text extraction failed schema validation ({val_err}). Escalating to VLM fallback.")
            else:
                return text_result

        # 3. Fallback Escalation to Multimodal VLM
        if image_bytes_list:
            logger.info("Executing Multimodal VLM fallback escalation.")
            vlm_payload = MultimodalPayload(
                prompt=prompt,
                image_bytes_list=image_bytes_list,
            )
            return await self.vlm_extractor.extract_multimodal(vlm_payload)

        return text_result
