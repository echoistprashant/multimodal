"""Unit tests for Phase 9 Part 9.3: Multimodal VLM Extraction and Orchestrator Fallback."""

import asyncio
from app.extraction.orchestrator import HybridExtractionOrchestrator
from app.extraction.prompt_builder import ExtractionPromptBuilder
from app.extraction.schema import LLMExtractionResult
from app.extraction.vlm_extractor import MultimodalVLMExtractor
from app.routing.schema import RouteType
from app.schemas.invoice import InvoiceSchema


def test_direct_vlm_routing() -> None:
    """Verify pages with RouteType.VLM directly invoke the multimodal vision model."""
    async def _run() -> None:
        doc_text = "Complex scanned invoice diagram with handwriting"
        prompt = ExtractionPromptBuilder.from_model(InvoiceSchema, doc_text)

        orchestrator = HybridExtractionOrchestrator(
            vlm_extractor=MultimodalVLMExtractor(model_name="mock-gemini-vision")
        )
        fake_img = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"

        result = await orchestrator.extract_document(
            prompt=prompt,
            route=RouteType.VLM,
            image_bytes_list=[fake_img],
            target_schema_cls=InvoiceSchema,
        )

        assert result.success is True
        assert result.model_name == "mock-gemini-vision"
        assert result.parsed_json["invoice_number"] == "INV-VLM-2026"
        assert result.parsed_json["total_amount"] == 3450.00

    asyncio.run(_run())


def test_text_to_vlm_fallback_on_schema_failure() -> None:
    """Verify failing text extraction automatically escalates to Multimodal VLM."""
    async def _run() -> None:
        doc_text = "Corrupted unparseable raw characters"
        prompt = ExtractionPromptBuilder.from_model(InvoiceSchema, doc_text)

        # Mock text extractor that returns incomplete invalid payload (missing total_amount & vendor)
        class FailingTextExtractor:
            async def extract(self, p: object) -> LLMExtractionResult:
                return LLMExtractionResult(
                    raw_response='{"partial": "only"}',
                    parsed_json={"partial": "only"},
                    model_name="mock-text-failing",
                    success=True,
                )

        orchestrator = HybridExtractionOrchestrator(
            text_extractor=FailingTextExtractor(),
            vlm_extractor=MultimodalVLMExtractor(model_name="mock-fallback-vlm"),
        )
        fake_img = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"

        result = await orchestrator.extract_document(
            prompt=prompt,
            route=RouteType.NATIVE,
            image_bytes_list=[fake_img],
            target_schema_cls=InvoiceSchema,
        )

        # Fallback to VLM should have succeeded
        assert result.model_name == "mock-fallback-vlm"
        assert result.parsed_json["invoice_number"] == "INV-VLM-2026"

    asyncio.run(_run())
