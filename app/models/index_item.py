"""IndexItem Multimodal Search Relational Model.

Represents multimodal index entities (text blocks, table rows, figure captions, page images)
with pgvector embedding vectors for hybrid dense/lexical search.
"""

import uuid
from typing import Any
from sqlalchemy import CheckConstraint, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin

# Import pgvector Vector type with graceful fallback
try:
    from pgvector.sqlalchemy import Vector
    VectorType: Any = Vector(1024)
except ImportError:
    VectorType = JSON


class IndexItem(Base, TimestampMixin):
    """Multimodal vector and lexical index entity."""

    __tablename__ = "index_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_no: Mapped[int] = mapped_column(Integer, nullable=False)
    block_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("blocks.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Modality: text | table_row | figure_desc | page_image
    modality: Mapped[str] = mapped_column(String(32), nullable=False)
    text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    bbox: Mapped[list[float]] = mapped_column(JSON, default=list, nullable=False)

    # Vector embedding
    embedding: Mapped[Any] = mapped_column(VectorType, nullable=True)
    embedding_model: Mapped[str] = mapped_column(String(64), default="BAAI/bge-m3", nullable=False)

    __table_args__ = (
        CheckConstraint(
            "modality IN ('text', 'table_row', 'figure_desc', 'page_image')",
            name="ck_index_item_modality",
        ),
    )
