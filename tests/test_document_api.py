"""Integration tests for Phase 3: Document Upload and API Management."""

import asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.validation import detect_mime_type, sanitize_filename, validate_file_payload
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app

# In-memory async SQLite engine for isolated integration testing
test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db() -> AsyncSession:  # type: ignore[misc]
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db_session] = override_get_db


def setup_module() -> None:
    """Initialize database tables in test sqlite memory."""
    async def _init_db() -> None:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(_init_db())


def test_mime_sniffer_and_validation() -> None:
    """Verify MIME sniffer distinguishes valid PDF from invalid binaries."""
    valid_pdf = b"%PDF-1.4 sample content"
    assert detect_mime_type(valid_pdf) == "application/pdf"

    valid_png = b"\x89PNG\r\n\x1a\nimage data"
    assert detect_mime_type(valid_png) == "image/png"

    clean_name = sanitize_filename("../../../malicious_file.pdf")
    assert clean_name == "malicious_file.pdf"

    mime, name = validate_file_payload("receipt.pdf", valid_pdf)
    assert mime == "application/pdf"
    assert name == "receipt.pdf"


def test_upload_and_status_lifecycle() -> None:
    """Verify upload, duplicate detection, metadata retrieval, and deletion flow."""
    async def _test() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            pdf_bytes = b"%PDF-1.4 dummy invoice for testing purpose"
            files = {"file": ("test_invoice.pdf", pdf_bytes, "application/pdf")}
            headers = {"X-Tenant-ID": "tenant_test_1"}

            # 1. Upload valid document
            res = await client.post("/api/v1/documents", files=files, headers=headers)
            assert res.status_code == 202
            data = res.json()
            doc_id = data["id"]
            assert data["filename"] == "test_invoice.pdf"
            assert data["mime_type"] == "application/pdf"
            assert data["is_duplicate"] is False

            # 2. Upload duplicate file -> should return is_duplicate = True
            files_dup = {"file": ("test_invoice.pdf", pdf_bytes, "application/pdf")}
            res_dup = await client.post("/api/v1/documents", files=files_dup, headers=headers)
            assert res_dup.status_code == 202
            dup_data = res_dup.json()
            assert dup_data["id"] == doc_id
            assert dup_data["is_duplicate"] is True

            # 3. Retrieve document status
            res_get = await client.get(f"/api/v1/documents/{doc_id}", headers=headers)
            assert res_get.status_code == 200
            status_data = res_get.json()
            assert status_data["id"] == doc_id
            assert status_data["status"] == "uploaded"

            # 4. List documents
            res_list = await client.get("/api/v1/documents", headers=headers)
            assert res_list.status_code == 200
            list_data = res_list.json()
            assert list_data["total"] >= 1

            # 5. Delete document
            res_del = await client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
            assert res_del.status_code == 204

            # 6. Verify 404 after deletion
            res_404 = await client.get(f"/api/v1/documents/{doc_id}", headers=headers)
            assert res_404.status_code == 404

    asyncio.run(_test())
