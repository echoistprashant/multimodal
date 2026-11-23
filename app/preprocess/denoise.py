"""Image Grayscale and Gaussian Denoising Preprocessing.

Enhances degraded document scans by converting RGB to single-channel luminance
and removing high-frequency salt-and-pepper noise before OCR.
"""

import io
from PIL import Image, ImageFilter

from app.core.logging import get_logger

logger = get_logger("app.preprocess.denoise")


def convert_to_grayscale(image_bytes: bytes) -> bytes:
    """Convert RGB/RGBA document scan image to 8-bit grayscale."""
    with Image.open(io.BytesIO(image_bytes)) as img:
        gray = img.convert("L")
        buf = io.BytesIO()
        gray.save(buf, format="PNG")
        return buf.getvalue()


def apply_gaussian_denoise(image_bytes: bytes, radius: float = 1.0) -> bytes:
    """Apply Gaussian spatial smoothing to reduce sensor and scanner noise."""
    with Image.open(io.BytesIO(image_bytes)) as img:
        gray = img.convert("L") if img.mode != "L" else img
        smoothed = gray.filter(ImageFilter.GaussianBlur(radius=radius))
        buf = io.BytesIO()
        smoothed.save(buf, format="PNG")
        return buf.getvalue()
