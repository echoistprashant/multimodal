"""Visual Edge Density and Gradient Energy Analyzer.

Uses OpenCV Canny edge detection and Laplacian gradients to assess image sharpness,
edge concentration, and document clutter.
"""

from typing import Union
import cv2
import numpy as np
from PIL import Image


def _to_grayscale_array(image: Union[Image.Image, np.ndarray]) -> np.ndarray:
    """Convert input PIL Image or numpy array to a single-channel 8-bit grayscale array."""
    if isinstance(image, Image.Image):
        gray_img = image.convert("L")
        return np.array(gray_img, dtype=np.uint8)

    if isinstance(image, np.ndarray):
        if image.ndim == 2:
            return image.astype(np.uint8)
        if image.ndim == 3:
            if image.shape[2] == 4:
                return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    raise ValueError(f"Unsupported image type: {type(image)}")


def compute_edge_density(
    image: Union[Image.Image, np.ndarray],
    canny_low: int = 50,
    canny_high: int = 150,
) -> tuple[float, float]:
    """Compute edge density and gradient energy of the rendered page image.

    Args:
        image: PIL Image or OpenCV ndarray.
        canny_low: Lower hysteresis threshold for Canny edge detector.
        canny_high: Higher hysteresis threshold for Canny edge detector.

    Returns:
        tuple[edge_density, gradient_energy]:
            - edge_density: Ratio of edge pixels to total pixels [0.0, 1.0].
            - gradient_energy: Mean Laplacian absolute energy (sharpness/texture metric).
    """
    gray = _to_grayscale_array(image)
    total_pixels = gray.size
    if total_pixels == 0:
        return 0.0, 0.0

    # Canny Edge Detection
    edges = cv2.Canny(gray, threshold1=canny_low, threshold2=canny_high)
    edge_pixels = int(np.count_nonzero(edges))
    edge_density = round(edge_pixels / total_pixels, 4)

    # Laplacian Gradient Energy
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    gradient_energy = round(float(np.mean(np.abs(laplacian))), 4)

    return edge_density, gradient_energy
