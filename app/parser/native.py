"""Native Digital PDF Parser.

Extracts embedded digital text layers, word bounding boxes, and font metadata
using pdfplumber, converting raw coordinates into normalized [0, 1] tokens.
"""

import io
import pdfplumber
from app.core.logging import get_logger
from app.parser.schema import BoundingBox, PageParseResult, Token

logger = get_logger("app.parser.native")


class NativePDFParser:
    """Extracts digital text and bounding boxes directly from digital vector PDFs."""

    def parse_page(self, pdf_bytes: bytes, page_no: int) -> PageParseResult:
        """Extract tokens and normalized coordinates from a specific page."""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            page_index = page_no - 1
            if page_index < 0 or page_index >= len(pdf.pages):
                raise IndexError(f"Page {page_no} out of bounds")

            page = pdf.pages[page_index]
            width_pt = float(page.width)
            height_pt = float(page.height)

            words = page.extract_words(
                x_tolerance=3,
                y_tolerance=3,
                keep_blank_chars=False,
                use_text_flow=True,
            )

            tokens: list[Token] = []
            for w in words:
                text = w.get("text", "").strip()
                if not text:
                    continue

                # pdfplumber coordinates: x0, top, x1, bottom with top-left origin
                x0 = max(0.0, min(1.0, float(w["x0"]) / width_pt))
                y0 = max(0.0, min(1.0, float(w["top"]) / height_pt))
                x1 = max(0.0, min(1.0, float(w["x1"]) / width_pt))
                y1 = max(0.0, min(1.0, float(w["bottom"]) / height_pt))

                tokens.append(
                    Token(
                        text=text,
                        bbox=BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1),
                        confidence=1.0,  # Native text has perfect 1.0 OCR confidence
                        page_no=page_no,
                        source="native",
                    )
                )

            raw_text = page.extract_text() or ""
            has_text_layer = len(tokens) >= 5 and len(raw_text.strip()) >= 20

            return PageParseResult(
                page_no=page_no,
                width_pt=width_pt,
                height_pt=height_pt,
                tokens=tokens,
                raw_text=raw_text,
                has_text_layer=has_text_layer,
            )
