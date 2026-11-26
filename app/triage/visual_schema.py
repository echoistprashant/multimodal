"""Visual Complexity and Image Analysis Schema.

Defines data contracts for visual edge density, graphical region detection,
and multimodal triage scoring.
"""

from pydantic import BaseModel, ConfigDict, Field


class VisualComplexityScore(BaseModel):
    """Metrics assessing visual complexity of a rendered document page."""

    model_config = ConfigDict(frozen=True)

    edge_density: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Ratio of edge pixels to total image pixels.",
    )
    gradient_energy: float = Field(
        ...,
        ge=0.0,
        description="Mean Laplacian or Sobel gradient energy across the page.",
    )
    has_complex_graphics: bool = Field(
        ...,
        description="Flag indicating presence of charts, diagrams, or dense graphic regions.",
    )
    graphics_regions: list[tuple[float, float, float, float]] = Field(
        default_factory=list,
        description="List of normalized [x0, y0, x1, y1] bounding boxes containing non-text graphics.",
    )
    complexity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized composite visual complexity score between 0.0 and 1.0.",
    )
    recommended_mode: str = Field(
        default="ocr",
        description="Recommended pathway: 'native', 'ocr', or 'vlm'.",
    )
