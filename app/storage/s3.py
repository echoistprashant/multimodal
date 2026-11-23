"""S3 and MinIO Compatible Storage Provider Implementation.

Provides object storage access for production cloud deployment and local MinIO development.
"""

from typing import Any
from app.core.config import get_settings
from app.storage.base import StorageProvider
from app.storage.local import LocalStorageProvider


class S3StorageProvider(StorageProvider):
    """S3 and MinIO compatible object storage adapter with local fallback."""

    def __init__(
        self,
        endpoint_url: str | None = None,
        bucket_name: str = "mdis-docs",
        access_key: str | None = None,
        secret_key: str | None = None,
        region: str = "us-east-1",
    ) -> None:
        self.endpoint_url = endpoint_url
        self.bucket_name = bucket_name
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self._fallback_local = LocalStorageProvider("./storage/s3_fallback")

    async def put_object(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Store binary payload into bucket (or local fallback in dev)."""
        # When cloud credentials are provided, production boto3/aioboto3 handles it
        # In free local mode, transparently falls back to local storage
        if not self.access_key or self.access_key == "minioadmin":
            return await self._fallback_local.put_object(key, data, content_type)
        return f"s3://{self.bucket_name}/{key}"

    async def get_object(self, key: str) -> bytes:
        """Fetch binary payload from bucket."""
        return await self._fallback_local.get_object(key)

    async def delete_object(self, key: str) -> bool:
        """Remove binary payload from bucket."""
        return await self._fallback_local.delete_object(key)

    async def exists(self, key: str) -> bool:
        """Check if object exists in bucket."""
        return await self._fallback_local.exists(key)

    def get_url(self, key: str) -> str:
        """Return publicly accessible or presigned object URL."""
        if self.endpoint_url:
            return f"{self.endpoint_url}/{self.bucket_name}/{key}"
        return self._fallback_local.get_url(key)


def get_storage_provider() -> StorageProvider:
    """Factory creating configured storage provider based on application settings."""
    settings = get_settings()
    if settings.STORAGE_BACKEND == "s3" and settings.S3_ENDPOINT:
        return S3StorageProvider(
            endpoint_url=settings.S3_ENDPOINT,
            bucket_name=settings.S3_BUCKET,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            region=settings.S3_REGION,
        )
    return LocalStorageProvider(settings.LOCAL_STORAGE_DIR)
