"""Storage Provider Abstract Protocol.

Defines the contract for object storage providers (Local disk, MinIO, AWS S3)
to ensure pluggability and zero vendor lock-in.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class StorageProvider(Protocol):
    """Abstract protocol for file and binary artifact storage."""

    async def put_object(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Persist binary payload at the specified storage key and return reference path."""
        ...

    async def get_object(self, key: str) -> bytes:
        """Retrieve binary payload for the given storage key."""
        ...

    async def delete_object(self, key: str) -> bool:
        """Delete object at the given key. Returns True if deleted, False otherwise."""
        ...

    async def exists(self, key: str) -> bool:
        """Check whether an object exists at the specified key."""
        ...

    def get_url(self, key: str) -> str:
        """Return accessible URL or URI path for the stored object."""
        ...
