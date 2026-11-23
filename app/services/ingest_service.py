"""Document Ingestion Service Module.

Coordinates document validation, SHA-256 content deduplication,
storage persistence, and database registration.
"""

import hashlib
import uuid
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.validation import validate_file_payload
from app.models.document import Document
from app.repositories.document_repo import DocumentRepository
from app.storage.base import StorageProvider

logger = get_logger("app.services.ingest")


@dataclass
class IngestResult:
    """Outcome of document ingestion."""

    document: Document
    is_duplicate: bool


class DocumentIngestService:
    """Service encapsulating the document ingestion lifecycle."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageProvider,
    ) -> None:
        self.session = session
        self.storage = storage
        self.repo = DocumentRepository(session)
        self.settings = get_settings()

    async def ingest_document(
        self,
        tenant_id: str,
        filename: str,
        content: bytes,
    ) -> IngestResult:
        """Validate, deduplicate, persist, and register an incoming document file."""
        # 1. Validate size and binary magic bytes
        mime_type, clean_filename = validate_file_payload(
            filename=filename,
            data=content,
            max_size_bytes=self.settings.MAX_FILE_SIZE_BYTES,
        )

        # 2. Compute cryptographically secure content hash (SHA-256)
        sha256_hash = hashlib.sha256(content).hexdigest()

        # 3. Idempotent check: Has this exact file already been ingested for this tenant/version?
        existing_doc = await self.repo.get_by_hash(
            tenant_id=tenant_id,
            sha256=sha256_hash,
            pipeline_version="v1.0",
        )
        if existing_doc:
            logger.info(
                f"Duplicate document detected for tenant [{tenant_id}] with sha256={sha256_hash[:8]}",
                extra={"document_id": str(existing_doc.id), "tenant_id": tenant_id},
            )
            return IngestResult(document=existing_doc, is_duplicate=True)

        # 4. Generate structured storage path
        storage_key = f"tenants/{tenant_id}/docs/{sha256_hash[:12]}/{clean_filename}"

        # 5. Persist raw binary to storage provider (immutable)
        try:
            await self.storage.put_object(
                key=storage_key,
                data=content,
                content_type=mime_type,
            )
        except Exception as err:
            logger.error(f"Failed to write document to storage: {err}", exc_info=True)
            raise

        # 6. Create database entity record inside safe transaction block
        try:
            new_doc = Document(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                filename=clean_filename,
                mime_type=mime_type,
                sha256=sha256_hash,
                storage_key=storage_key,
                page_count=0,
                status="uploaded",
                pipeline_version="v1.0",
            )
            saved_doc = await self.repo.create(new_doc)
            await self.session.commit()
        except Exception as db_err:
            await self.session.rollback()
            # Clean up storage orphan
            await self.storage.delete_object(storage_key)
            logger.error(f"Database registration failed, storage cleaned: {db_err}", exc_info=True)
            raise

        logger.info(
            f"Successfully ingested new document {clean_filename} (id={saved_doc.id}) for tenant {tenant_id}",
            extra={"document_id": str(saved_doc.id), "tenant_id": tenant_id},
        )
        return IngestResult(document=saved_doc, is_duplicate=False)
