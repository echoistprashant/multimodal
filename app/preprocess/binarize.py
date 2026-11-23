"""Adaptive Binarization and Contrast Enhancement Module.

Converts grayscale document scans to crisp binary black-and-white (1-bit) images
using Otsu's thresholding algorithm to maximize OCR character recognition accuracy.
"""

import io
from PIL import Image, ImageOps

from app.core.logging import get_logger

logger = get_logger("app.preprocess.binarize")


def compute_otsu_threshold(img: Image.Image) -> int:
    """Calculate optimal global threshold separating foreground ink from background paper."""
    hist = img.histogram()
    total_pixels = img.width * img.height

    current_max = 0.0
    threshold = 128
    weight_background = 0
    sum_background = 0

    total_sum = sum(i * count for i, count in enumerate(hist))

    for t in range(256):
        weight_background += hist[t]
        if weight_background == 0:
            continue

        weight_foreground = total_pixels - weight_background
        if weight_foreground == 0:
            break

        sum_background += t * hist[t]
        mean_background = sum_background / weight_background
        mean_foreground = (total_sum - sum_background) / weight_foreground

        # Between-class variance
        between_variance = (
            weight_background
            * weight_foreground
            * ((mean_background - mean_foreground) ** 2)
        )

        if between_variance > current_max:
            current_max = between_variance
            threshold = t

    return threshold


def binarize_document(
    image_bytes: bytes,
    autocontrast: bool = True,
) -> bytes:
    """Perform Otsu threshold binarization on scanned page image."""
    with Image.open(io.BytesIO(image_bytes)) as img:
        gray = img.convert("L")
        if autocontrast:
            gray = ImageOps.autocontrast(gray, cutoff=2)

        threshold = compute_otsu_threshold(gray)
        # Binarize: pixels above threshold become white (255), below become black (0)
        binary = gray.point(lambda p: 255 if p > threshold else 0, mode="1")

        buf = io.BytesIO()
        binary.save(buf, format="PNG")
        logger.info(f"Applied Otsu binarization at threshold={threshold}")
        return buf.getvalue()
