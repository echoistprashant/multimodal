"""Triage and Routing Data Models.

Defines data contracts for text layer health evaluation, visual density scoring,
and cost-aware tier routing decisions.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class TextLayerHealth:
    """Quantitative assessment of embedded digital text layer quality."""

    has_text_layer: bool
    total_characters: int
    printable_ratio: float
    alpha_ratio: float
    dictionary_word_ratio: float
    is_garbled: bool
    health_score: float  # Composite score [0.0, 1.0]
