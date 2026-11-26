"""Schema Registry and Discovery API Endpoints."""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status

from app.schemas.registry import SchemaRegistry

router = APIRouter(prefix="/api/v1/schemas", tags=["Schema Registry"])


@router.get(
    "",
    response_model=List[Dict[str, Any]],
    summary="List all registered document schemas",
)
def list_schemas() -> List[Dict[str, Any]]:
    """Discover all supported document schemas, SemVer versions, and JSON schema definitions."""
    registry = SchemaRegistry.get_instance()
    return registry.list_schemas()


@router.get(
    "/{doc_type}",
    response_model=Dict[str, Any],
    summary="Get JSON Schema for a specific document category",
)
def get_schema(doc_type: str, version: str | None = None) -> Dict[str, Any]:
    """Retrieve full JSON Schema specification for prompt formatting and structured LLM extraction."""
    registry = SchemaRegistry.get_instance()
    schema_cls = registry.get_schema(doc_type=doc_type, version=version)

    if not schema_cls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema for document type '{doc_type}' (version={version}) not found in registry.",
        )

    return {
        "doc_type": doc_type.lower(),
        "version": version or "latest",
        "json_schema": schema_cls.model_json_schema(),
    }
