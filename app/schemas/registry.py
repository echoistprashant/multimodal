"""Thread-Safe Document Schema Registry.

Central catalog managing dynamic registration, schema resolution, and JSON Schema export
for domain document intelligence extraction models.
"""

import threading
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel

from app.schemas.invoice import InvoiceSchema
from app.schemas.receipt_medical import MedicalBillSchema, ReceiptSchema


class SchemaRegistry:
    """Thread-safe registry mapping document domain types and versions to Pydantic schemas."""

    _instance: Optional["SchemaRegistry"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._registry: Dict[str, Dict[str, Type[BaseModel]]] = {}
        self._lock = threading.RLock()
        self._register_default_schemas()

    @classmethod
    def get_instance(cls) -> "SchemaRegistry":
        """Singleton accessor for global schema registry."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _register_default_schemas(self) -> None:
        """Register built-in core enterprise document models."""
        self.register("invoice", InvoiceSchema, version="1.0.0")
        self.register("receipt", ReceiptSchema, version="1.0.0")
        self.register("medical_bill", MedicalBillSchema, version="1.0.0")

    def register(
        self,
        doc_type: str,
        schema_cls: Type[BaseModel],
        version: str = "1.0.0",
    ) -> None:
        """Register a Pydantic schema class under a document type and version."""
        norm_type = doc_type.strip().lower()
        with self._lock:
            if norm_type not in self._registry:
                self._registry[norm_type] = {}
            self._registry[norm_type][version] = schema_cls

    def get_schema(
        self,
        doc_type: str,
        version: Optional[str] = None,
    ) -> Optional[Type[BaseModel]]:
        """Retrieve schema class for document type. Defaults to highest SemVer if version is None."""
        norm_type = doc_type.strip().lower()
        with self._lock:
            versions_map = self._registry.get(norm_type)
            if not versions_map:
                return None

            if version is not None:
                return versions_map.get(version)

            # Return latest version sorted alphabetically / semver
            latest_version = sorted(versions_map.keys(), reverse=True)[0]
            return versions_map[latest_version]

    def list_schemas(self) -> List[Dict[str, Any]]:
        """List all registered schemas with metadata and JSON Schema specifications."""
        with self._lock:
            result = []
            for doc_type, versions in self._registry.items():
                for ver, cls in versions.items():
                    result.append({
                        "doc_type": doc_type,
                        "version": ver,
                        "description": cls.__doc__.strip() if cls.__doc__ else "",
                        "json_schema": cls.model_json_schema(),
                    })
            return result
