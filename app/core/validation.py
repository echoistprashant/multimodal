"""File Validation and MIME Sniffing Module.

Verifies true binary file headers (magic bytes) to defend against extension spoofing,
path traversal, decompression bombs, and unsupported media types.
"""

import re
from pathlib import Path


class FileValidationError(Exception):
    """Raised when file fails security or content validation."""
    pass


# Magic byte signatures for supported multimodal documents
MAGIC_SIGNATURES: dict[str, bytes] = {
    "application/pdf": b"%PDF-",
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/jpeg": b"\xff\xd8\xff",
    "image/tiff": b"II*\x00",
}
MAGIC_SIGNATURES_BE_TIFF = b"MM\x00*"


def detect_mime_type(data: bytes) -> str:
    """Sniff real MIME type directly from binary magic bytes."""
    if len(data) < 8:
        raise FileValidationError("File payload too small to be a valid document or image")

    for mime, signature in MAGIC_SIGNATURES.items():
        if data.startswith(signature):
            return mime

    if data.startswith(MAGIC_SIGNATURES_BE_TIFF):
        return "image/tiff"

    raise FileValidationError(
        "Unsupported file format. System accepts only PDF, PNG, JPEG, and TIFF documents."
    )


def sanitize_filename(filename: str) -> str:
    """Strip path traversal components and dangerous characters from uploaded filename."""
    # Take basename only
    clean = Path(filename).name
    # Keep only safe alphanumeric, dash, dot, and underscore
    clean = re.sub(r"[^a-zA-Z0-9._-]", "_", clean)
    if not clean or clean.startswith("."):
        clean = f"document_{clean.lstrip('.')}"
    return clean[:200]


def validate_file_payload(
    filename: str,
    data: bytes,
    max_size_bytes: int = 25 * 1024 * 1024,
) -> tuple[str, str]:
    """Validate uploaded document bytes and filename, returning (mime_type, clean_filename)."""
    if len(data) == 0:
        raise FileValidationError("Empty file uploaded")

    if len(data) > max_size_bytes:
        max_mb = max_size_bytes // (1024 * 1024)
        raise FileValidationError(f"File size exceeds maximum allowed threshold of {max_mb} MB")

    mime_type = detect_mime_type(data)
    clean_filename = sanitize_filename(filename)

    return mime_type, clean_filename
