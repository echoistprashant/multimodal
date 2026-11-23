"""Document Relational ORM Model.

Represents an ingested document file (PDF/Image) with metadata, SHA-256 fingerprint,
processing lifecycle status, and tenant isolation.
"""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, Float, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.page import Page


class Document(Base, TimestampMixin):
    """Document entity table representing uploaded files."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)

    page_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    doc_type: Mapped[str | None] = mapped_column(String(64), default=None, nullable=True)
    doc_type_confidence: Mapped[float | None] = mapped_column(Float, default=None, nullable=True)

    status: Mapped[str] = mapped_column(
        String(32),
        default="uploaded",
        nullable=False,
        index=True,
    )
    pipeline_version: Mapped[str] = mapped_column(String(32), default="v1.0", nullable=False)
    error_message: Mapped[str | None] = mapped_column(String, default=None, nullable=True)

    # Relationship to constituent pages
    pages: Mapped[list["Page"]] = relationship(
        "Page",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="Page.page_no",
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "sha256", "pipeline_version",
            name="uq_document_tenant_hash_version",
        ),
        CheckConstraint(
            "status IN ('uploaded', 'processing', 'needs_review', 'approved', 'failed')",
            name="ck_document_status",
        ),
    )
