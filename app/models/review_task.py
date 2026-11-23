"""ReviewTask Relational ORM Model.

Tracks human-in-the-loop review tickets generated for low-confidence,
ungrounded, or arithmetic validation failures.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.extracted_field import ExtractedField


class ReviewTask(Base, TimestampMixin):
    """Human review assignment item for field-level corrections."""

    __tablename__ = "review_tasks"

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
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extracted_fields.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        nullable=False,
        index=True,
    )
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(String(64), default=None, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(String(512), default=None, nullable=True)

    # Relationship to extracted field
    field: Mapped["ExtractedField"] = relationship("ExtractedField", back_populates="review_task")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'resolved', 'dismissed')",
            name="ck_review_task_status",
        ),
    )
