"""Document Repository Module.

Handles database access for Document entities, enforcing strict tenant isolation
and SHA-256 content deduplication per pipeline version.
"""

import uuid
from typing import Sequence
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


class DocumentRepository:
    """Repository handling SQL queries for Document persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(
        self,
        document_id: uuid.UUID,
        tenant_id: str,
    ) -> Document | None:
        """Fetch a document by primary key enforcing tenant isolation."""
        stmt = select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_hash(
        self,
        tenant_id: str,
        sha256: str,
        pipeline_version: str = "v1.0",
    ) -> Document | None:
        """Find an existing document by its content fingerprint to ensure idempotency."""
        stmt = select(Document).where(
            Document.tenant_id == tenant_id,
            Document.sha256 == sha256,
            Document.pipeline_version == pipeline_version,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, document: Document) -> Document:
        """Persist a new document record into the database."""
        self.session.add(document)
        await self.session.flush()
        await self.session.refresh(document)
        return document

    async def update_status(
        self,
        document_id: uuid.UUID,
        tenant_id: str,
        status: str,
        page_count: int | None = None,
        doc_type: str | None = None,
        doc_type_confidence: float | None = None,
        error_message: str | None = None,
    ) -> Document | None:
        """Update processing status and extracted high-level metadata."""
        values: dict[str, object] = {"status": status}
        if page_count is not None:
            values["page_count"] = page_count
        if doc_type is not None:
            values["doc_type"] = doc_type
        if doc_type_confidence is not None:
            values["doc_type_confidence"] = doc_type_confidence
        if error_message is not None:
            values["error_message"] = error_message

        stmt = (
            update(Document)
            .where(Document.id == document_id, Document.tenant_id == tenant_id)
            .values(**values)
            .returning(Document)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_documents(
        self,
        tenant_id: str,
        skip: int = 0,
        limit: int = 50,
        status: str | None = None,
    ) -> Sequence[Document]:
        """List paginated documents belonging to the authenticated tenant."""
        stmt = (
            select(Document)
            .where(Document.tenant_id == tenant_id)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if status:
            stmt = stmt.where(Document.status == status)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete(self, document_id: uuid.UUID, tenant_id: str) -> bool:
        """Delete document record, cascading to pages and fields."""
        doc = await self.get_by_id(document_id, tenant_id)
        if not doc:
            return False
        await self.session.delete(doc)
        await self.session.flush()
        return True
