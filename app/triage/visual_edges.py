"""Visual Edge Density and Gradient Energy Analyzer.

Uses NumPy and SciPy image gradient filters to assess sharpness,
edge concentration, and document clutter without requiring external binary dependencies.
"""

from typing import Union
import numpy as np
from PIL import Image
from scipy import ndimage


def _to_grayscale_array(image: Union[Image.Image, np.ndarray]) -> np.ndarray:
    """Convert input PIL Image or numpy array to a 2D float32 grayscale array [0, 255]."""
    if isinstance(image, Image.Image):
        gray_img = image.convert("L")
        return np.array(gray_img, dtype=np.float32)

    if isinstance(image, np.ndarray):
        if image.ndim == 2:
            return image.astype(np.float32)
        if image.ndim == 3:
            # Grayscale standard luminance weights (ITU-R 601-2)
            if image.shape[2] == 4:
                return (0.299 * image[:, :, 0] + 0.587 * image[:, :, 1] + 0.114 * image[:, :, 2]).astype(np.float32)
            return (0.299 * image[:, :, 0] + 0.587 * image[:, :, 1] + 0.114 * image[:, :, 2]).astype(np.float32)

    raise ValueError(f"Unsupported image type: {type(image)}")


def compute_edge_density(
    image: Union[Image.Image, np.ndarray],
    threshold: float = 40.0,
) -> tuple[float, float]:
    """Compute edge density and gradient energy of the rendered page image.

    Args:
        image: PIL Image or ndarray.
        threshold: Magnitude threshold for classifying a pixel as an edge.

    Returns:
        tuple[edge_density, gradient_energy]:
            - edge_density: Ratio of edge pixels to total pixels [0.0, 1.0].
            - gradient_energy: Mean gradient magnitude across the image.
    """
    gray = _to_grayscale_array(image)
    total_pixels = gray.size
    if total_pixels == 0:
        return 0.0, 0.0

    # Compute horizontal and vertical Sobel gradients
    sx = ndimage.sobel(gray, axis=1)
    sy = ndimage.sobel(gray, axis=0)
    sobel_mag = np.hypot(sx, sy)

    edge_pixels = int(np.count_nonzero(sobel_mag > threshold))
    edge_density = round(edge_pixels / total_pixels, 4)
    gradient_energy = round(float(np.mean(sobel_mag)), 4)

    return edge_density, gradient_energy
