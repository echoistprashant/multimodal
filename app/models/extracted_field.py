"""ExtractedField Relational ORM Model.

Represents an entity value extracted by LLM or VLM, with provenance
(page, normalized bounding box, source text), confidence, validation status, and review state.
"""

import uuid
from typing import Any, TYPE_CHECKING
from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.review_task import ReviewTask


class ExtractedField(Base, TimestampMixin):
    """Extracted entity field with strict provenance and validation audit."""

    __tablename__ = "extracted_fields"

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

    field_path: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    value: Mapped[Any] = mapped_column(JSON, nullable=True)
    normalized_value: Mapped[Any] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Provenance tracking
    page_no: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox: Mapped[list[float]] = mapped_column(JSON, default=list, nullable=False)  # [x0, y0, x1, y1]
    source_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    grounded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Validation and straight-through processing status
    validation_status: Mapped[str] = mapped_column(
        String(32),
        default="unchecked",
        nullable=False,
    )
    validation_messages: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    review_status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        nullable=False,
        index=True,
    )

    # Relationship to review tasks
    review_task: Mapped["ReviewTask"] = relationship(
        "ReviewTask",
        back_populates="field",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "validation_status IN ('valid', 'invalid', 'unchecked')",
            name="ck_field_validation_status",
        ),
        CheckConstraint(
            "review_status IN ('auto_approved', 'pending', 'corrected', 'confirmed')",
            name="ck_field_review_status",
        ),
    )
