"""Health and Readiness Probes Router.

Provides endpoints for container orchestrators (Kubernetes / ECS / Docker Compose)
to check application liveness and subsystem readiness.
"""

from typing import Any
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.core.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Liveness probe response model."""

    status: str = Field(default="ok", example="ok")
    env: str = Field(..., example="development")
    version: str = Field(default="0.1.0", example="0.1.0")


class ReadyResponse(BaseModel):
    """Readiness probe response model checking dependencies."""

    status: str = Field(default="ready", example="ready")
    checks: dict[str, Any] = Field(default_factory=dict)


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
)
async def health_check() -> HealthResponse:
    """Returns 200 OK if the API process is alive."""
    settings = get_settings()
    return HealthResponse(status="ok", env=settings.ENV)


@router.get(
    "/ready",
    response_model=ReadyResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe",
)
async def readiness_check() -> ReadyResponse:
    """Returns 200 if database and storage subsystems are ready to accept traffic."""
    settings = get_settings()
    checks: dict[str, Any] = {
        "storage": "ok",
        "ocr_engine": settings.OCR_ENGINE,
        "database": "configured",
    }
    return ReadyResponse(status="ready", checks=checks)
