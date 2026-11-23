"""Unit tests for Phase 1: Settings, Security, Middleware, and Probes."""

import asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.main import app


def test_settings_load() -> None:
    """Verify application configuration loads default attributes correctly."""
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.PROJECT_NAME == "Multimodal Document Intelligence System"
    assert settings.STORAGE_BACKEND in ("local", "s3")
    assert settings.MAX_FILE_SIZE_BYTES > 0


def test_password_hashing() -> None:
    """Verify bcrypt password hashing and verification."""
    password = "SecurePassword123!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_generation_and_validation() -> None:
    """Verify JWT access token generation, claims encoding, and decoding."""
    subject = "user_123"
    tenant_id = "tenant_abc"
    token = create_access_token(subject=subject, tenant_id=tenant_id, role="reviewer")

    payload = decode_access_token(token)
    assert payload is not None
    assert payload.sub == subject
    assert payload.tenant_id == tenant_id
    assert payload.role == "reviewer"


def test_health_probe() -> None:
    """Verify /health endpoint returns 200 OK and valid status."""
    async def _test() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "env" in data

    asyncio.run(_test())


def test_ready_probe() -> None:
    """Verify /ready endpoint returns 200 and subsystem checks."""
    async def _test() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
            assert "checks" in data

    asyncio.run(_test())


def test_request_id_middleware() -> None:
    """Verify middleware injects X-Request-ID header into responses."""
    async def _test() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert "x-request-id" in response.headers
            assert response.headers["x-request-id"].startswith("req_")

    asyncio.run(_test())
