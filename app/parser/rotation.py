"""Page Rotation and Orientation Detection Module.

Detects document rotation (0°, 90°, 180°, 270°) using embedded PDF metadata
and visual orientation heuristics to prevent extraction failures on rotated scans.
"""

import io
from PIL import Image
import pypdfium2 as pdfium

from app.core.logging import get_logger

logger = get_logger("app.parser.rotation")


def get_pdf_page_rotation(pdf_bytes: bytes, page_no: int) -> int:
    """Read declared rotation angle in degrees from PDF dictionary metadata."""
    pdf = pdfium.PdfDocument(pdf_bytes)
    try:
        page_index = page_no - 1
        if 0 <= page_index < len(pdf):
            page = pdf[page_index]
            return int(page.get_rotation())
        return 0
    finally:
        pdf.close()


def detect_image_orientation_heuristic(image_bytes: bytes) -> int:
    """Inspect image dimensions to detect obvious landscape scans."""
    with Image.open(io.BytesIO(image_bytes)) as img:
        width, height = img.size
        # Most documents are portrait (height > width). If width is significantly larger,
        # it may be rotated 90 or 270 degrees.
        if width > 1.3 * height:
            return 90
        return 0
