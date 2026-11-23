"""Database Index Definitions and Vector Optimization Helpers.

Provides DDL scripts and SQLAlchemy index constructs for HNSW approximate
nearest neighbor (ANN) vector search and full-text search (GIN).
"""

from sqlalchemy import DDL, Index, event
from app.models.index_item import IndexItem

# HNSW vector cosine search index DDL definition
CREATE_VECTOR_EXTENSION_SQL = "CREATE EXTENSION IF NOT EXISTS vector;"
CREATE_PG_TRGM_SQL = "CREATE EXTENSION IF NOT EXISTS pg_trgm;"

# HNSW Index with tuned parameters (m=16, ef_construction=64)
hnsw_index = Index(
    "ix_index_items_embedding_hnsw",
    IndexItem.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_cosine_ops"},
)

# Composite B-tree index for tenant-isolated document retrieval
tenant_doc_page_index = Index(
    "ix_index_items_tenant_doc_page",
    IndexItem.tenant_id,
    IndexItem.document_id,
    IndexItem.page_no,
)


def register_index_events() -> None:
    """Attach DDL events to create extensions before table creation."""
    event.listen(
        IndexItem.metadata,
        "before_create",
        DDL(CREATE_VECTOR_EXTENSION_SQL),
    )
    event.listen(
        IndexItem.metadata,
        "before_create",
        DDL(CREATE_PG_TRGM_SQL),
    )
