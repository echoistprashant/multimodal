# Multimodal Document Intelligence System (MDIS)

> Production-Grade OCR, Layout Analysis, Structured Entity Extraction, Grounding & Multimodal RAG Platform.

---

## 🌟 Executive Overview
**MDIS (Multimodal Document Intelligence System)** is an enterprise AI engineering platform designed to convert heterogeneous, unstructured, and visually complex documents (scanned invoices, receipts, tax forms, financial reports with tables and charts) into:
1. **Validated, Schema-Constrained Structured Data (JSON)** with verifiable bounding-box provenance.
2. **A High-Accuracy Multimodal Knowledge Base (RAG)** enabling semantic question answering with page-level citations and visual bounding-box highlights.
3. **Deterministic Human-in-the-Loop Review Flows** triggered automatically by arithmetic inconsistencies, low OCR confidence, or ungrounded model extractions.

---

## 🏗️ Architecture & Processing Pipeline

```
Raw Document (PDF / Scan / Photo)
       │
       ▼
[Stage 1: Ingestion & Rendering]
       ├── MIME Sniffing & File Validation (Magic Bytes)
       ├── SHA-256 Hashing & Deduplication
       ├── High-Res Rasterization (200-300 DPI)
       └── Digital Text Extraction & Coordinate Normalization
       │
       ▼
[Stage 2: Preprocessing & OCR Engine]
       ├── Grayscale & Gaussian Denoising
       ├── Automatic Deskewing & Baseline Alignment
       ├── Adaptive Otsu Binarization
       └── Multi-Engine OCR (PaddleOCR / docTR / Tesseract)
       │
       ▼
[Stage 3: Triage & Cost-Aware Routing (Phase 6)]
       ├── Text Layer Health & Garble Analysis (Printable & Word Quality Ratios)
       ├── Visual Complexity & Edge Energy Density (Scanned vs. Diagram)
       ├── Deterministic 3-Tier Router (Native vs. Local OCR vs. Multimodal VLM)
       └── Telemetry & Financial Cost Accounting (Tracking USD Savings)
       │
       ▼
[Stage 4: Layout Analysis & Table Reconstruction (Phase 7)]
       ├── Horizontal & Vertical Projection Profiling
       ├── Recursive XY-Cut Algorithm for Multi-Column Reading Order
       ├── Morphological Bordered & Whitespace Borderless Table Detectors
       ├── Table Grid Cell Matrix Reconstruction & Column Header Inference
       └── Layout-Aware Serialization (GFM Markdown & Grounded HTML5)
       │
       ▼
[Stage 5: Document Classification & Schema Registry (Phase 8)]
       ├── Enterprise Pydantic Schemas (Invoices, Receipts, Medical Bills)
       ├── Hybrid Classifier (Diagnostic Regex Rules + Spatial Layout Aspect Ratios)
       ├── Thread-Safe Schema Registry & SemVer Compatibility Migrations
       ├── Field Extraction Guidance Generator & Prompt Annotation
       └── Anti-Hallucination Normalization (Null-if-Absent, Currency Coercion)
       │
       ▼
[Stage 6: Structured Extraction Engine (Phase 9)]
       ├── Dynamic Prompt Builder with JSON Schema Injection & Delimiter Safety
       ├── Text-Based Structured LLM Extractor with Exponential Backoff Retry
       ├── Multimodal Vision VLM Extractor (Gemini Vision / Qwen2-VL)
       ├── Hybrid Extraction Orchestrator with Automatic Multimodal Fallback
       ├── Resilient JSON Repair Parser (Fenced Markdown, Trailing Commas)
       └── Multi-Page Item Stitcher & Cross-Page Line Item Deduplication
```

---

## 🚀 Completed Phases Roadmap (Phases 1 to 9)

### Phase 1: Project Setup & Repository Scaffold
- **Part 1.1**: Clean directory structure, dependency definitions in `pyproject.toml`, and `.gitignore`.
- **Part 1.2**: Typed configuration management via `pydantic-settings` (`app/core/config.py`).
- **Part 1.3**: Structured JSON logging and `X-Request-ID` correlation middleware (`app/core/logging.py`, `app/api/middleware.py`).
- **Part 1.4**: FastAPI application factory and `/health`, `/ready` liveness probes (`app/main.py`, `app/api/v1/health.py`).

### Phase 2: Database & Storage Setup
- **Part 2.1**: Relational ORM models for `Document`, `Page`, `Block`, `ExtractedField`, and `ReviewTask` (`app/models/`).
- **Part 2.2**: Vector database search model `IndexItem` with pgvector integration and HNSW indexing (`app/models/index_item.py`, `app/db/indexes.py`).
- **Part 2.3**: Abstract storage protocol (`StorageProvider`) with `LocalStorageProvider` and `S3StorageProvider` for MinIO/S3 (`app/storage/`).
- **Part 2.4**: Alembic database migrations scaffolding and `DocumentRepository` with SHA-256 deduplication.

### Phase 3: API & Document Upload
- **Part 3.1**: Pydantic DTO contracts for document upload, status polling, and pagination (`app/schemas/document.py`).
- **Part 3.2**: Binary magic bytes sniffer and filename sanitization (`app/core/validation.py`).
- **Part 3.3**: Async ingestion service with transactional persistence and background task queue (`app/services/ingest_service.py`, `app/queue/`).
- **Part 3.4**: RESTful API endpoints (`POST /api/v1/documents`, `GET /api/v1/documents`, `GET /api/v1/documents/{id}`, `DELETE /api/v1/documents/{id}`).

### Phase 4: Page Rendering & Text Parsing
- **Part 4.1**: PDF page rasterization engine (200 DPI) using `pypdfium2` and thumbnail generator (`app/pipeline/render.py`, `app/pipeline/page_manager.py`).
- **Part 4.2**: Native digital text parser extracting words and font coordinates (`app/parser/native.py`).
- **Part 4.3**: Universal coordinate normalization converting point/pixel values to resolution-independent `[0.0, 1.0]` bounding boxes (`app/geometry/normalization.py`).
- **Part 4.4**: Spatial bounding box operations: Intersection-over-Union (IoU), box union, and rotation matrix transforms (`app/geometry/spatial.py`, `app/geometry/transform.py`, `app/pipeline/stage1_render_extract.py`).

### Phase 5: Image Preprocessing & OCR Engine Setup
- **Part 5.1**: Computer vision preprocessing filters: Grayscale conversion, Gaussian smoothing, and deskewing (`app/preprocess/denoise.py`, `app/preprocess/deskew.py`).
- **Part 5.2**: Adaptive Otsu binarization for low-contrast scans (`app/preprocess/binarize.py`).
- **Part 5.3**: Open-source OCR engine adapters (`TesseractOCREngine` and `DeepOCREngine` for PaddleOCR/docTR) and token line aggregator (`app/ocr/`).
- **Part 5.4**: Quantitative evaluation metrics: Character Error Rate (CER) and Word Error Rate (WER) using Levenshtein distance, and Stage 2 OCR pipeline worker (`app/evaluation/ocr_metrics.py`, `app/pipeline/stage2_ocr_worker.py`).

### Phase 6: Triage & Cost-Aware Routing
- **Part 6.1**: Embedded text layer health analyzer: Printable character ratio, font encoding anomaly detection, and dictionary word density (`app/triage/`).
- **Part 6.2**: Visual complexity scoring: Sobel edge density, gradient energy, and non-text diagram/chart contour detection (`app/triage/visual_edges.py`, `app/triage/visual_regions.py`).
- **Part 6.3**: Multi-tier decision router: Cost and latency estimator balancing Native ($0), Local OCR ($0), and VLM vision pathways (`app/routing/router.py`, `app/routing/cost_estimator.py`).
- **Part 6.4**: Routing telemetry collector and API: Persisting route choices and querying cost savings (`GET /api/v1/documents/{id}/routing`).

### Phase 7: Layout Analysis & Table Extraction
- **Part 7.1**: Projection profiler and recursive XY-Cut algorithm for natural multi-column reading order reconstruction (`app/layout/xy_cut.py`).
- **Part 7.2**: Dual-strategy table detection: Morphological kernels for bordered tables and whitespace projection clustering for borderless tables (`app/tables/`).
- **Part 7.3**: Structured table grid reconstructor: Cell spanning resolution, row hierarchy alignment, and semantic column header inference (`app/tables/grid_reconstructor.py`, `app/tables/header_inference.py`).
- **Part 7.4**: Layout-aware text serializers (GitHub Flavored Markdown and HTML5 with `data-bbox` visual grounding annotations) and Stage 3 pipeline worker (`app/layout/`, `app/pipeline/stage3_layout_worker.py`).

### Phase 8: Document Classification & Pydantic Schemas
- **Part 8.1**: Production domain schemas: `InvoiceSchema`, `ReceiptSchema`, and `MedicalBillSchema` with mathematical line item and tax balance constraints (`app/schemas/`).
- **Part 8.2**: Hybrid document classifier: Diagnostic lexical pattern matching combined with spatial paper aspect ratio cues (`app/classifier/`).
- **Part 8.3**: Thread-safe `SchemaRegistry` and SemVer compatibility validator with RESTful discovery endpoints (`GET /api/v1/schemas`, `GET /api/v1/schemas/{doc_type}`).
- **Part 8.4**: Extraction guidance generator for schema fields and anti-hallucination sanitization rules (`null_if_absent`, currency cleaning).

### Phase 9: Structured Extraction (LLM / VLM)
- **Part 9.1**: Prompt engineering engine: Dynamic JSON schema injection, few-shot examples, and collision-resistant XML delimiter wrapping against prompt injection (`app/extraction/prompt_builder.py`, `app/extraction/prompt_safety.py`).
- **Part 9.2**: Text-based LLM extractor: Support for OpenAI / local inference with exponential backoff retry handler and zero-cost deterministic mock fallback (`app/extraction/text_llm.py`, `app/extraction/retry.py`).
- **Part 9.3**: Multimodal Vision VLM engine: Gemini Vision / Qwen2-VL support with `HybridExtractionOrchestrator` providing automatic multimodal fallback upon schema validation failure (`app/extraction/vlm_extractor.py`, `app/extraction/orchestrator.py`).
- **Part 9.4**: Resilient JSON repair parser (recovering markdown-fenced, single-quoted, or trailing-comma JSON), multi-page line item stitcher (`MultiPageItemStitcher`), and Stage 4 pipeline worker (`app/pipeline/stage4_extraction_worker.py`).

---

## 🧪 Testing & Verification

The test suite runs with **zero external network, cloud, or database dependencies**, ensuring 100% offline reproducibility across all phases:

```bash
# Run entire test suite (76 tests passing)
python -m pytest

# Run with test coverage
python -m pytest --cov=app
```

**Test Suite Coverage Summary (76 unit & integration tests):**
- `tests/test_health_and_config.py`: Settings, JWT authentication, bcrypt hashing, and API health probes.
- `tests/test_storage_and_models.py`: Local storage provider, S3 fallback, path traversal guards, and database ORM entity instantiation.
- `tests/test_document_api.py`: Multipart document upload, idempotent duplicate detection, metadata retrieval, pagination, and deletion.
- `tests/test_parser_and_geometry.py`: Bounding box coordinate normalization, IoU calculations, box unioning, and 90°/180°/270° spatial transformations.
- `tests/test_ocr_and_preprocessing.py`: Grayscale conversion, Gaussian denoising, Otsu binarization, deskewing, token line aggregation, and CER/WER error rate computation.
- `tests/test_triage_health.py`: Embedded PDF text layer health, printable character ratio, and font encoding anomaly detection.
- `tests/test_triage_visual.py`: Edge density, gradient energy, and diagram/chart non-text region detection.
- `tests/test_routing_decisions.py`: Multi-tier routing heuristics, forced policy overrides, and financial cost savings estimation.
- `tests/test_routing_telemetry_api.py`: Routing telemetry repository caching and `GET /api/v1/documents/{id}/routing` API endpoint.
- `tests/test_layout_xy_cut.py`: Horizontal/vertical projection histograms and recursive XY-Cut reading order sorting.
- `tests/test_tables_detection.py`: Morphological line detection for bordered tables and whitespace alignment for borderless tables.
- `tests/test_tables_grid.py`: 2D table grid reconstruction, cell bounding boxes, and column header inference.
- `tests/test_layout_worker.py`: Stage 3 worker integration, Markdown table serialization, and HTML grounding markup.
- `tests/test_domain_schemas.py`: Validation of commercial Invoice, retail Receipt, and healthcare Medical Bill Pydantic models.
- `tests/test_classifier.py`: Hybrid lexical keyword and spatial aspect ratio classification across all document categories.
- `tests/test_schema_registry_api.py`: Dynamic schema registration, SemVer compatibility checks, and `GET /api/v1/schemas` discovery endpoints.
- `tests/test_field_guidance.py`: Automated field guidance generation, prompt rules, null value cleaning, and currency coercion.
- `tests/test_extraction_prompts.py`: Schema prompt formatting and collision-resistant delimiter wrapping for prompt injection defense.
- `tests/test_text_llm.py`: Text LLM extraction execution and exponential backoff retry handler with transient recovery.
- `tests/test_extraction_orchestrator.py`: Direct VLM routing and automatic multimodal VLM fallback upon text validation failure.
- `tests/test_stage4_worker.py`: Markdown JSON repair, cross-page line item stitching, and end-to-end Stage 4 extraction pipeline.

---

## 🛠️ Free-of-Cost Tech Stack

| Layer | Component | 100% Free / Open-Source Tool |
| :--- | :--- | :--- |
| **Language & API** | Python 3.12, FastAPI, Pydantic v2 | Open-source |
| **Relational DB** | PostgreSQL + pgvector | Self-hosted Docker container |
| **Object Storage** | MinIO (S3-compatible) | Self-hosted Docker container |
| **Task Queue** | Redis | Self-hosted Docker container |
| **PDF & Vision** | pypdfium2, Pillow, NumPy, SciPy | Open-source Python libraries |
| **OCR Engines** | PaddleOCR / docTR / Tesseract | Open-source |
| **Embeddings** | BAAI/bge-m3, OpenCLIP | Hugging Face local models |
| **VLM / LLM** | Google Gemini 1.5 Flash (Free Tier) / Qwen2-VL | Free Tier / Ollama local |
| **Observability** | Self-hosted Langfuse / OpenTelemetry | Open-source Docker stack |

---

## 📄 License
This project is licensed under the MIT License.
