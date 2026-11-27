"""Master End-to-End Pipeline Orchestrator (Triage -> Layout -> Extraction -> Grounding -> Validation -> RAG)."""

from typing import Dict, List, Optional

from app.core.logging import get_logger
from app.observability.tracer import PipelineStageTracer
from app.pipeline.orchestrator_schema import (
    FullPipelineResult,
    PipelineExecutionConfig,
    PipelinePageInput,
)
from app.pipeline.stage3_layout_worker import Stage3LayoutResult, Stage3LayoutWorker
from app.pipeline.stage4_extraction_worker import Stage4ExtractionWorker
from app.pipeline.stage5_grounding_worker import Stage5GroundingWorker
from app.pipeline.stage6_validation_worker import Stage6ValidationWorker
from app.pipeline.stage7_index_worker import Stage7IndexWorker
from app.repositories.routing_repo import RoutingRepository
from app.routing.router import DocumentTriageRouter
from app.routing.telemetry import RoutingTelemetryAccumulator
from app.tables.grid_schema import StructuredTable
from app.triage.density import analyze_text_layer_health
from app.triage.visual_schema import VisualComplexityScore

logger = get_logger("app.pipeline.master_orchestrator")


class MasterPipelineOrchestrator:
    """Runs a document end-to-end across all intelligent MDIS stages."""

    def __init__(self) -> None:
        self.triage_router = DocumentTriageRouter()
        self.layout_worker = Stage3LayoutWorker()
        self.extraction_worker = Stage4ExtractionWorker()
        self.grounding_worker = Stage5GroundingWorker()
        self.validation_worker = Stage6ValidationWorker()
        self.index_worker = Stage7IndexWorker()
        self.routing_repo = RoutingRepository()

    async def run(
        self,
        document_id: str,
        pages: List[PipelinePageInput],
        config: Optional[PipelineExecutionConfig] = None,
    ) -> FullPipelineResult:
        """Execute full multimodal pipeline from page tokens to grounded validation and RAG indexing."""
        cfg = config or PipelineExecutionConfig()
        tracer = PipelineStageTracer(document_id=document_id)
        logger.info(f"Starting MasterPipelineOrchestrator for doc={document_id} ({len(pages)} pages)")

        # 1. Triage & Routing
        telemetry = RoutingTelemetryAccumulator(document_id=document_id)
        page_routes = {}
        with tracer.trace_stage("triage_routing"):
            for p in pages:
                page_txt = p.raw_text or " ".join(str(t.get("text", "")) for t in p.tokens)
                text_health = analyze_text_layer_health(page_txt, token_count=len(p.tokens))
                visual = VisualComplexityScore(
                    edge_density=0.02,
                    gradient_energy=1.5,
                    has_complex_graphics=False,
                    graphics_regions=[],
                    complexity_score=0.10,
                    recommended_mode="native",
                )
                decision = self.triage_router.route_page(text_health, visual)
                telemetry.record_decision(p.page_no, decision)
                page_routes[p.page_no] = decision.route

            routing_report = telemetry.generate_report()
            self.routing_repo.save_report(routing_report)

        # 2. Layout & Table Extraction (Stage 3)
        layout_results: List[Stage3LayoutResult] = []
        all_tables: List[StructuredTable] = []
        pages_tokens: Dict[int, List[dict]] = {}
        with tracer.trace_stage("layout_tables"):
            for p in pages:
                pages_tokens[p.page_no] = p.tokens
                l_res = self.layout_worker.process_page(page_number=p.page_no, tokens=p.tokens)
                layout_results.append(l_res)
                all_tables.extend(l_res.tables)

        # 3. Classification & Structured Extraction (Stage 4)
        with tracer.trace_stage("structured_extraction"):
            pages_payload = [
                {
                    "page_number": lr.page_number,
                    "markdown_content": lr.markdown_content or pages[idx].raw_text,
                    "route": page_routes.get(lr.page_number),
                }
                for idx, lr in enumerate(layout_results)
            ]
            ext_res = await self.extraction_worker.process_document(
                document_id=document_id,
                pages_content=pages_payload,
                forced_doc_type=cfg.forced_doc_type,
            )

        # 4. Grounding & Hallucination Audit (Stage 5)
        with tracer.trace_stage("grounding_provenance"):
            grd_res = self.grounding_worker.process_document(
                document_id=document_id,
                extracted_data=ext_res.extracted_data,
                pages_tokens=pages_tokens,
                tables=all_tables,
            )

        # 5. Deterministic Validation & STP Gateway (Stage 6)
        with tracer.trace_stage("validation_stp"):
            val_res = self.validation_worker.process_document(
                document_id=document_id,
                extracted_data=ext_res.extracted_data,
                provenance_matches=grd_res.matches,
                hallucination_report=grd_res.audit_report,
            )

        # 6. Multimodal RAG Indexing (Stage 7)
        total_chunks = 0
        if cfg.enable_rag_indexing:
            with tracer.trace_stage("rag_indexing"):
                for lr in layout_results:
                    idx_res = self.index_worker.index_page(
                        document_id=document_id,
                        page_no=lr.page_number,
                        blocks=lr.blocks,
                        tables=lr.tables,
                        tenant_id=cfg.tenant_id,
                    )
                    total_chunks += idx_res.chunks_indexed

        return FullPipelineResult(
            document_id=document_id,
            doc_type=ext_res.doc_type,
            approval_decision=val_res.verdict.decision,
            composite_confidence=val_res.confidence.calibrated_score,
            hallucination_rate=grd_res.audit_report.hallucination_rate,
            chunks_indexed=total_chunks,
            extracted_data=ext_res.extracted_data,
            routing_report=routing_report,
            stage_traces=tracer.spans,
        )
