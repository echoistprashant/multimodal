"""Integration tests for Phase 8 Part 8.3: Schema Registry, Versioning, and API Endpoints."""

from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.main import app
from app.schemas.registry import SchemaRegistry
from app.schemas.versioning import SemVer, check_schema_compatibility, migrate_document_payload

client = TestClient(app)


def test_schema_registry_dynamic_registration() -> None:
    """Verify dynamic schema registration and retrieval."""
    registry = SchemaRegistry.get_instance()

    class CustomTaxDocument(BaseModel):
        tax_year: int
        filer_ssn: str

    registry.register("custom_tax", CustomTaxDocument, version="1.0.0")
    retrieved = registry.get_schema("custom_tax", version="1.0.0")
    assert retrieved is CustomTaxDocument

    # Check case-insensitivity
    retrieved_case = registry.get_schema("CUSTOM_TAX")
    assert retrieved_case is CustomTaxDocument


def test_semver_and_compatibility() -> None:
    """Verify SemVer comparison rules and backward compatibility checks."""
    v10 = SemVer("1.0.0")
    v11 = SemVer("1.1.0")
    v20 = SemVer("2.0.0")

    assert v10 < v11 < v20
    assert check_schema_compatibility("1.1.0", "1.0.0") is True
    assert check_schema_compatibility("2.0.0", "1.0.0") is False

    payload = {"invoice_number": "INV-1"}
    migrated = migrate_document_payload(payload, from_version="1.0.0", to_version="1.1.0")
    assert migrated["schema_version"] == "1.1.0"
    assert migrated["currency"] == "USD"


def test_api_list_schemas() -> None:
    """Verify GET /api/v1/schemas returns all registered models."""
    response = client.get("/api/v1/schemas")
    assert response.status_code == 200
    schemas = response.json()
    types = [s["doc_type"] for s in schemas]
    assert "invoice" in types
    assert "receipt" in types
    assert "medical_bill" in types


def test_api_get_schema_detail() -> None:
    """Verify GET /api/v1/schemas/{doc_type} returns valid JSON schema."""
    response = client.get("/api/v1/schemas/invoice")
    assert response.status_code == 200
    data = response.json()
    assert data["doc_type"] == "invoice"
    assert "properties" in data["json_schema"]
    assert "invoice_number" in data["json_schema"]["properties"]

    # 404 for unknown schema
    err_res = client.get("/api/v1/schemas/unknown_contract_xyz")
    assert err_res.status_code == 404
