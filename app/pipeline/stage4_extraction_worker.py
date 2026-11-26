"""Stage 4 Pipeline Worker: End-to-End Structured Extraction and Multi-Page Stitching.

Orchestrates document classification, schema lookup, hybrid LLM/VLM extraction,
anti-hallucination sanitization, and multi-page line item stitching.
"""

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.classifier.hybrid_classifier import HybridDocumentClassifier
from app.core.logging import get_logger
from app.extraction.orchestrator import HybridExtractionOrchestrator
from app.extraction.prompt_builder import ExtractionPromptBuilder
from app.extraction.stitcher import MultiPageItemStitcher
from app.routing.schema import RouteType
from app.schemas.registry import SchemaRegistry

logger = get_logger("app.pipeline.stage4_extraction_worker")


class Stage4ExtractionResult(BaseModel):
    """Unified extracted output for a complete multi-page document."""

    model_config = ConfigDict(frozen=True)

    document_id: str
    doc_type: str
    classification_confidence: float = Field(ge=0.0, le=1.0)
    extracted_data: Dict[str, Any]
    total_pages_processed: int = Field(ge=1)
    latency_ms: float = Field(ge=0.0)


class Stage4ExtractionWorker:
    """Worker orchestrating structured extraction across all document pages."""

    def __init__(
        self,
        classifier: Optional[HybridDocumentClassifier] = None,
        orchestrator: Optional[HybridExtractionOrchestrator] = None,
        stitcher: Optional[MultiPageItemStitcher] = None,
        schema_registry: Optional[SchemaRegistry] = None,
    ) -> None:
        self.classifier = classifier or HybridDocumentClassifier()
        self.orchestrator = orchestrator or HybridExtractionOrchestrator()
        self.stitcher = stitcher or MultiPageItemStitcher()
        self.schema_registry = schema_registry or SchemaRegistry.get_instance()

    async def process_document(
        self,
        document_id: str,
        pages_content: List[Dict[str, Any]],
        forced_doc_type: Optional[str] = None,
    ) -> Stage4ExtractionResult:
        """Execute Stage 4 extraction on all pages of a document."""
        start_time = time.perf_counter()
        logger.info(f"Executing Stage 4 Extraction on document '{document_id}' with {len(pages_content)} pages.")

        # 1. Aggregate consolidated document text
        consolidated_text = "\n\n".join(
            p.get("markdown_content") or p.get("text", "") for p in pages_content
        )

        # 2. Document Classification
        if forced_doc_type:
            doc_type = forced_doc_type.lower()
            confidence = 1.0
        else:
            cls_result = self.classifier.classify_document(consolidated_text)
            doc_type = cls_result.predicted_type.value
            confidence = cls_result.confidence

        # Default to invoice if unknown
        if doc_type == "unknown":
            doc_type = "invoice"

        # 3. Look up schema in registry
        schema_cls = self.schema_registry.get_schema(doc_type)

        # 4. Extract each page
        page_results: List[Dict[str, Any]] = []
        for p in pages_content:
            p_text = p.get("markdown_content") or p.get("text", "")
            route_val = p.get("route", RouteType.NATIVE)
            img_bytes = p.get("image_bytes")

            if schema_cls:
                prompt = ExtractionPromptBuilder.from_model(schema_cls, p_text)
            else:
                prompt = ExtractionPromptBuilder().build_prompt(
                    # Generic prompt fallback
                    context=None  # Handled safely by builder
                )

            res = await self.orchestrator.extract_document(
                prompt=prompt,
                route=route_val,
                image_bytes_list=[img_bytes] if img_bytes else [],
                target_schema_cls=schema_cls,
            )
            if res.success and res.parsed_json:
                page_results.append(res.parsed_json)

        # 5. Multi-Page Stitching
        final_stitched = self.stitcher.stitch_pages(page_results, target_schema_cls=schema_cls)
        latency = round((time.perf_counter() - start_time) * 1000, 2)

        return Stage4ExtractionResult(
            document_id=document_id,
            doc_type=doc_type,
            classification_confidence=confidence,
            extracted_data=final_stitched,
            total_pages_processed=len(pages_content),
            latency_ms=latency,
        )
