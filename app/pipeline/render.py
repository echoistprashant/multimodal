"""PDF Page Rasterization Engine.

Renders PDF document pages into high-resolution images (PNG) at target DPI
for visual layout analysis, OCR fallback, and human review inspection.
"""

import io
from dataclasses import dataclass
from typing import Sequence
import pypdfium2 as pdfium
from PIL import Image

from app.core.logging import get_logger

logger = get_logger("app.pipeline.render")


@dataclass
class RasterizedPage:
    """Represents a rendered PDF page image with resolution metadata."""

    page_no: int
    image_bytes: bytes
    width_px: int
    height_px: int
    dpi: int
    rotation: int = 0


class PDFRasterizer:
    """Renders PDF bytes into high-quality rasterized page images using pypdfium2."""

    def __init__(self, dpi: int = 200) -> None:
        self.dpi = dpi
        # pypdfium scale factor: 72 points per inch default
        self.scale = dpi / 72.0

    def get_page_count(self, pdf_bytes: bytes) -> int:
        """Read total page count of a PDF document."""
        pdf = pdfium.PdfDocument(pdf_bytes)
        try:
            return len(pdf)
        finally:
            pdf.close()

    def render_page(self, pdf_bytes: bytes, page_no: int) -> RasterizedPage:
        """Render a single 1-based page index to PNG image bytes."""
        pdf = pdfium.PdfDocument(pdf_bytes)
        try:
            page_index = page_no - 1
            if page_index < 0 or page_index >= len(pdf):
                raise IndexError(f"Page {page_no} is out of bounds for document with {len(pdf)} pages")

            page = pdf[page_index]
            rotation = page.get_rotation()
            bitmap = page.render(scale=self.scale)
            pil_image = bitmap.to_pil()

            buffer = io.BytesIO()
            pil_image.save(buffer, format="PNG", optimize=True)
            img_bytes = buffer.getvalue()

            return RasterizedPage(
                page_no=page_no,
                image_bytes=img_bytes,
                width_px=pil_image.width,
                height_px=pil_image.height,
                dpi=self.dpi,
                rotation=rotation,
            )
        finally:
            pdf.close()

    def render_all_pages(self, pdf_bytes: bytes) -> Sequence[RasterizedPage]:
        """Rasterize all pages of a PDF document."""
        pdf = pdfium.PdfDocument(pdf_bytes)
        try:
            total_pages = len(pdf)
            results: list[RasterizedPage] = []
            for idx in range(total_pages):
                page_no = idx + 1
                page = pdf[idx]
                rotation = page.get_rotation()
                bitmap = page.render(scale=self.scale)
                pil_image = bitmap.to_pil()

                buf = io.BytesIO()
                pil_image.save(buf, format="PNG", optimize=True)

                results.append(
                    RasterizedPage(
                        page_no=page_no,
                        image_bytes=buf.getvalue(),
                        width_px=pil_image.width,
                        height_px=pil_image.height,
                        dpi=self.dpi,
                        rotation=rotation,
                    )
                )
            return results
        finally:
            pdf.close()
