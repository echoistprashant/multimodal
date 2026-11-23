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
[Stage 3: Layout Analysis & Table Reconstruction]
       ├── Semantic Block Detection (Headers, Columns, Lists)
       ├── Table Detection & Cell Grid Recovery
       └── Layout-Aware Text Serialization (Markdown / HTML)
       │
       ▼
[Stage 4: Structured Extraction & Grounding]
       ├── Schema-Constrained Extraction (Pydantic Models)
       ├── Bounding-Box Provenance & Spatial Alignment
       └── Hallucination Guard (Flagging Ungrounded Fields)
       │
       ▼
[Stage 5: Validation & Auto-Approval Gateway]
       ├── Deterministic Arithmetic Checks (Line items sum = subtotal)
       ├── Confidence Calibration & Composite Scoring
       ├── Auto-Approval (Straight-Through Processing)
       └── Human-in-the-Loop Review Queue
       │
       ▼
[Stage 6: Multimodal RAG & Query Interface]
       ├── Multi-Modal Chunking (Tables, Text, Figures)
       ├── Vector & Lexical Hybrid Search (HNSW + BM25)
       └── Visual Q&A with Region-Level Citations
```

---

## 🚀 Completed Phases Roadmap (Phases 1 to 5)

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

---

## 🧪 Testing & Verification

The test suite runs with zero external network or database dependencies using in-memory asynchronous engines:

```bash
# Run entire test suite
python -m pytest

# Run with test coverage
python -m pytest --cov=app
```

**Test Coverage Summary:**
- `tests/test_health_and_config.py`: Settings, JWT authentication, bcrypt hashing, and API health probes.
- `tests/test_storage_and_models.py`: Local storage provider, S3 fallback, path traversal guards, and database ORM entity instantiation.
- `tests/test_document_api.py`: Multipart document upload, idempotent duplicate detection, metadata retrieval, pagination, and deletion.
- `tests/test_parser_and_geometry.py`: Bounding box coordinate normalization, IoU calculations, box unioning, and 90°/180°/270° spatial transformations.
- `tests/test_ocr_and_preprocessing.py`: Grayscale conversion, Gaussian denoising, Otsu binarization, deskewing, token line aggregation, and CER/WER error rate computation.

---

## 🛠️ Free-of-Cost Tech Stack

| Layer | Component | 100% Free / Open-Source Tool |
| :--- | :--- | :--- |
| **Language & API** | Python 3.12, FastAPI, Pydantic v2 | Open-source |
| **Relational DB** | PostgreSQL + pgvector | Self-hosted Docker container |
| **Object Storage** | MinIO (S3-compatible) | Self-hosted Docker container |
| **Task Queue** | Redis | Self-hosted Docker container |
| **PDF & Vision** | pypdfium2, pdfplumber, Pillow, OpenCV | Open-source Python libraries |
| **OCR Engines** | PaddleOCR / docTR / Tesseract | Open-source |
| **Embeddings** | BAAI/bge-m3, OpenCLIP | Hugging Face local models |
| **VLM / LLM** | Google Gemini 1.5 Flash (Free Tier) / Qwen2-VL | Free Tier / Ollama local |
| **Observability** | Self-hosted Langfuse / OpenTelemetry | Open-source Docker stack |

---

## 📄 License
This project is licensed under the MIT License.
