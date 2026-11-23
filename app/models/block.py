"""Block Relational ORM Model.

Represents a visual or layout segment (paragraph, heading, table, chart)
with normalized bounding box coordinates and semantic reading order.
"""

import uuid
from typing import Any, TYPE_CHECKING
from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.page import Page


class Block(Base, TimestampMixin):
    """Block entity representing layout segments within a document page."""

    __tablename__ = "blocks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type: Mapped[str] = mapped_column(
        String(32),
        default="text",
        nullable=False,
    )
    reading_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Normalized spatial bounding box: [x0, y0, x1, y1] in range [0.0, 1.0]
    x0: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    y0: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    x1: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    y1: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Block content (text and structured token payload)
    text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    content: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationship
    page: Mapped["Page"] = relationship("Page", back_populates="blocks")

    __table_args__ = (
        CheckConstraint(
            "type IN ('text', 'heading', 'table', 'figure', 'chart', 'list', 'header', 'footer')",
            name="ck_block_type",
        ),
    )
