"""OCR Package.

Exports abstract interface and concrete OCR engine implementations.
"""

from app.ocr.base import OCREngine
from app.ocr.mock_or_deep import DeepOCREngine
from app.ocr.tesseract import TesseractOCREngine


def get_ocr_engine(engine_name: str = "tesseract") -> OCREngine:
    """Factory creating OCR engine by name identifier."""
    if engine_name.lower() in ("paddleocr", "doctr"):
        return DeepOCREngine(engine_name=engine_name)
    return TesseractOCREngine()


__all__ = [
    "DeepOCREngine",
    "OCREngine",
    "TesseractOCREngine",
    "get_ocr_engine",
]
