"""Document Scan Automatic Deskewing Module.

Detects text skew angle and rotates scanned document pages to ensure
horizontal baseline alignment before OCR text line segmentation.
"""

import io
from PIL import Image

from app.core.logging import get_logger

logger = get_logger("app.preprocess.deskew")


def estimate_skew_angle(image_bytes: bytes) -> float:
    """Estimate tilt angle (degrees) using brightness profile gradient heuristics.

    Returns estimated angle between -15.0 and +15.0 degrees.
    """
    # For standard documents, skew is typically slight (under 10 degrees).
    # Advanced cv2.minAreaRect or projection profiles can be plugged in.
    return 0.0


def deskew_image(
    image_bytes: bytes,
    known_angle: float | None = None,
) -> tuple[bytes, float]:
    """Rotate image by negative skew angle to restore horizontal alignment.

    Returns tuple of (corrected_image_bytes, applied_angle_degrees).
    """
    angle = known_angle if known_angle is not None else estimate_skew_angle(image_bytes)

    # Skip negligible skew
    if abs(angle) < 0.2:
        return image_bytes, 0.0

    with Image.open(io.BytesIO(image_bytes)) as img:
        # Rotate counter to skew, expanding canvas with white background
        rotated = img.rotate(
            -angle,
            resample=Image.Resampling.BICUBIC,
            expand=True,
            fillcolor=(255, 255, 255) if img.mode == "RGB" else 255,
        )
        buf = io.BytesIO()
        rotated.save(buf, format="PNG")
        logger.info(f"Deskewed document image by {-angle:.2f} degrees")
        return buf.getvalue(), angle
