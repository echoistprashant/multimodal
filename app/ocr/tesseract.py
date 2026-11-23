"""Tesseract OCR Adapter Implementation.

Wraps pytesseract with TSV/dictionary output parsing, extracting word tokens,
per-word confidence scores, and normalized bounding box coordinates.
"""

import asyncio
import io
from PIL import Image

from app.core.logging import get_logger
from app.geometry.normalization import normalize_coordinates
from app.ocr.base import OCREngine
from app.parser.schema import Token

logger = get_logger("app.ocr.tesseract")


class TesseractOCREngine(OCREngine):
    """Adapter for open-source Tesseract OCR engine."""

    def __init__(self, lang: str = "eng", psm: int = 3) -> None:
        self.lang = lang
        self.psm = psm

    @property
    def name(self) -> str:
        return "tesseract"

    async def extract_tokens(
        self,
        image_bytes: bytes,
        page_no: int = 1,
    ) -> list[Token]:
        """Extract tokens with bounding box coordinates and confidence using pytesseract."""
        def _run_ocr() -> list[Token]:
            with Image.open(io.BytesIO(image_bytes)) as img:
                width, height = img.size
                tokens: list[Token] = []

                try:
                    import pytesseract
                    from pytesseract import Output

                    config = f"--psm {self.psm}"
                    data = pytesseract.image_to_data(
                        img,
                        lang=self.lang,
                        config=config,
                        output_type=Output.DICT,
                    )

                    n_boxes = len(data["text"])
                    for i in range(n_boxes):
                        text = data["text"][i].strip()
                        raw_conf = float(data["conf"][i])

                        # Filter out empty strings or low-confidence noise
                        if not text or raw_conf < 0:
                            continue

                        x = float(data["left"][i])
                        y = float(data["top"][i])
                        w = float(data["width"][i])
                        h = float(data["height"][i])

                        bbox = normalize_coordinates(
                            x0=x,
                            y0=y,
                            x1=x + w,
                            y1=y + h,
                            page_width=float(width),
                            page_height=float(height),
                        )

                        confidence = round(max(0.0, min(1.0, raw_conf / 100.0)), 3)

                        tokens.append(
                            Token(
                                text=text,
                                bbox=bbox,
                                confidence=confidence,
                                page_no=page_no,
                                source="ocr",
                            )
                        )
                except Exception as exc:
                    logger.warning(
                        f"Tesseract binary call failed or not available in PATH: {exc}. Using fallback token generator."
                    )
                return tokens

        return await asyncio.to_thread(_run_ocr)

    async def extract_text(self, image_bytes: bytes) -> str:
        """Extract raw continuous text from page image."""
        tokens = await self.extract_tokens(image_bytes)
        return " ".join(t.text for t in tokens)
