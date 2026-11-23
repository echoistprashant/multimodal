"""OCR Engine Abstract Interface.

Standardizes OCR engine implementations (Tesseract, PaddleOCR, docTR, Mock)
behind a unified Protocol emitting normalized spatial Tokens.
"""

from typing import Protocol, runtime_checkable
from app.parser.schema import Token


@runtime_checkable
class OCREngine(Protocol):
    """Abstract protocol for optical character recognition engines."""

    @property
    def name(self) -> str:
        """Name identifier of the OCR engine."""
        ...

    async def extract_tokens(
        self,
        image_bytes: bytes,
        page_no: int = 1,
    ) -> list[Token]:
        """Process page image and return individual tokens with normalized bounding boxes and confidences."""
        ...

    async def extract_text(self, image_bytes: bytes) -> str:
        """Extract continuous plain text string from page image."""
        ...
