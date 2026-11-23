"""Unit tests for Phase 2: Storage Providers, ORM Models, and Repositories."""

import asyncio
import tempfile
import uuid
from pathlib import Path
import pytest

from app.models.block import Block
from app.models.document import Document
from app.models.extracted_field import ExtractedField
from app.models.index_item import IndexItem
from app.models.page import Page
from app.models.review_task import ReviewTask
from app.storage.local import LocalStorageProvider
from app.storage.s3 import S3StorageProvider


def test_local_storage_lifecycle() -> None:
    """Verify local storage provider save, retrieve, check exists, and delete flow."""
    async def _test() -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            provider = LocalStorageProvider(base_dir=tmpdir)
            key = "docs/sample.txt"
            payload = b"Hello Multimodal Document Intelligence System!"

            # Put object
            path_str = await provider.put_object(key, payload)
            assert Path(path_str).exists()

            # Check exists
            assert await provider.exists(key) is True
            assert await provider.exists("docs/non_existent.txt") is False

            # Get object
            read_bytes = await provider.get_object(key)
            assert read_bytes == payload

            # URL
            url = provider.get_url(key)
            assert url.startswith("file://")

            # Delete
            deleted = await provider.delete_object(key)
            assert deleted is True
            assert await provider.exists(key) is False

    asyncio.run(_test())


def test_local_storage_path_traversal_prevention() -> None:
    """Verify LocalStorageProvider rejects directory traversal attempts."""
    async def _test() -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            provider = LocalStorageProvider(base_dir=tmpdir)
            with pytest.raises(ValueError, match="Path traversal detected"):
                await provider.put_object("../../../etc/passwd", b"malicious")

    asyncio.run(_test())


def test_s3_storage_local_fallback() -> None:
    """Verify S3StorageProvider fallback to local filesystem when dev credentials used."""
    async def _test() -> None:
        provider = S3StorageProvider(bucket_name="test-bucket", access_key="minioadmin")
        key = "uploads/test.pdf"
        data = b"%PDF-1.4 test document content"

        stored_path = await provider.put_object(key, data)
        assert stored_path is not None
        assert await provider.exists(key) is True
        fetched = await provider.get_object(key)
        assert fetched == data
        await provider.delete_object(key)

    asyncio.run(_test())


def test_orm_models_instantiation() -> None:
    """Verify database models instantiate with expected attributes and default values."""
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        tenant_id="tenant-alpha",
        filename="invoice_2026.pdf",
        mime_type="application/pdf",
        sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        storage_key="uploads/tenant-alpha/invoice_2026.pdf",
        status="uploaded",
        pipeline_version="v1.0",
    )
    assert doc.id == doc_id
    assert doc.status == "uploaded"
    assert doc.pipeline_version == "v1.0"

    page = Page(
        document_id=doc_id,
        page_no=1,
        width_px=1240,
        height_px=1754,
        dpi=200,
        route="ocr",
    )
    assert page.page_no == 1
    assert page.route == "ocr"

    block = Block(
        page_id=page.id,
        type="table",
        reading_order=2,
        x0=0.1,
        y0=0.3,
        x1=0.9,
        y1=0.7,
        text="Item | Qty | Price\nWidget | 2 | $50.00",
    )
    assert block.type == "table"
    assert block.reading_order == 2

    field = ExtractedField(
        document_id=doc_id,
        field_path="total_amount",
        value="100.00",
        normalized_value=100.00,
        confidence=0.98,
        page_no=1,
        bbox=[0.75, 0.85, 0.90, 0.88],
        source_text="$100.00",
        grounded=True,
        validation_status="valid",
        review_status="auto_approved",
    )
    assert field.grounded is True
    assert field.review_status == "auto_approved"

    task = ReviewTask(
        document_id=doc_id,
        field_id=field.id,
        status="pending",
        priority=1,
    )
    assert task.status == "pending"

    index_item = IndexItem(
        tenant_id="tenant-alpha",
        document_id=doc_id,
        page_no=1,
        modality="table_row",
        text="Widget | 2 | $50.00",
        bbox=[0.1, 0.3, 0.9, 0.35],
        embedding_model="BAAI/bge-m3",
    )
    assert index_item.modality == "table_row"
    assert index_item.embedding_model == "BAAI/bge-m3"
