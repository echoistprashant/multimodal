"""Local Filesystem Storage Provider Implementation.

Provides asynchronous file persistence on local disk with automatic directory creation.
"""

import asyncio
from pathlib import Path
from app.storage.base import StorageProvider


class LocalStorageProvider(StorageProvider):
    """Local disk-backed storage adapter."""

    def __init__(self, base_dir: str | Path = "./storage") -> None:
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        """Resolve storage key to safe local absolute path."""
        # Sanitize relative path traversal
        clean_key = key.lstrip("/\\")
        target = (self.base_dir / clean_key).resolve()
        if not str(target).startswith(str(self.base_dir)):
            raise ValueError(f"Path traversal detected: {key}")
        return target

    async def put_object(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Save binary data to local filesystem."""
        path = self._resolve_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        def _write() -> None:
            path.write_bytes(data)

        await asyncio.to_thread(_write)
        return str(path)

    async def get_object(self, key: str) -> bytes:
        """Read binary data from local filesystem."""
        path = self._resolve_path(key)
        if not path.exists():
            raise FileNotFoundError(f"Storage object not found: {key}")

        def _read() -> bytes:
            return path.read_bytes()

        return await asyncio.to_thread(_read)

    async def delete_object(self, key: str) -> bool:
        """Delete local file if it exists."""
        path = self._resolve_path(key)
        if not path.exists():
            return False

        def _delete() -> None:
            path.unlink(missing_ok=True)

        await asyncio.to_thread(_delete)
        return True

    async def exists(self, key: str) -> bool:
        """Check if local file exists."""
        path = self._resolve_path(key)
        return await asyncio.to_thread(path.exists)

    def get_url(self, key: str) -> str:
        """Return local file URI."""
        return f"file://{self._resolve_path(key).as_posix()}"
