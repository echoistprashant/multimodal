"""Page Relational ORM Model.

Represents an individual rasterized or digital page within a parent document,
tracking resolution, triage route decision, and constituent visual blocks.
"""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.block import Block
    from app.models.document import Document


class Page(Base, TimestampMixin):
    """Page entity table representing single document pages."""

    __tablename__ = "pages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_no: Mapped[int] = mapped_column(Integer, nullable=False)
    width_px: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    height_px: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dpi: Mapped[int] = mapped_column(Integer, default=200, nullable=False)
    image_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Triage decision: native | ocr | vlm
    route: Mapped[str | None] = mapped_column(String(32), default=None, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, default=None, nullable=True)
    rotation: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="pages")
    blocks: Mapped[list["Block"]] = relationship(
        "Block",
        back_populates="page",
        cascade="all, delete-orphan",
        order_by="Block.reading_order",
    )

    __table_args__ = (
        UniqueConstraint("document_id", "page_no", name="uq_page_document_page_no"),
        CheckConstraint(
            "route IS NULL OR route IN ('native', 'ocr', 'vlm')",
            name="ck_page_route",
        ),
    )
