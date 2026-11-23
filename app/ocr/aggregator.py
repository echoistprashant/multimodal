"""OCR Token Aggregation and Line Reconstruction Module.

Groups scattered word-level tokens into horizontal lines and paragraph blocks
based on vertical coordinate proximity and reading flow.
"""

from typing import Sequence
from app.geometry.spatial import union_bounding_boxes
from app.parser.schema import BoundingBox, Token


class TokenAggregator:
    """Reconstructs text lines and paragraphs from raw word tokens."""

    def __init__(self, line_y_threshold: float = 0.015) -> None:
        self.line_y_threshold = line_y_threshold

    def group_tokens_into_lines(self, tokens: Sequence[Token]) -> list[list[Token]]:
        """Cluster word tokens into lines based on vertical overlap."""
        if not tokens:
            return []

        # Sort primarily by vertical position (y0), secondarily by horizontal (x0)
        sorted_tokens = sorted(tokens, key=lambda t: (t.bbox.y0, t.bbox.x0))

        lines: list[list[Token]] = []
        current_line: list[Token] = [sorted_tokens[0]]

        for token in sorted_tokens[1:]:
            last_token = current_line[-1]
            # Check if token vertically aligns with current line within tolerance
            vertical_diff = abs(token.bbox.y0 - last_token.bbox.y0)
            if vertical_diff <= self.line_y_threshold:
                current_line.append(token)
            else:
                # Sort line left-to-right before finalizing
                current_line.sort(key=lambda t: t.bbox.x0)
                lines.append(current_line)
                current_line = [token]

        if current_line:
            current_line.sort(key=lambda t: t.bbox.x0)
            lines.append(current_line)

        return lines

    def serialize_lines_to_text(self, lines: list[list[Token]]) -> list[tuple[str, BoundingBox]]:
        """Convert grouped token lines into line strings and unified bounding boxes."""
        results: list[tuple[str, BoundingBox]] = []
        for line in lines:
            line_text = " ".join(t.text for t in line)
            line_bbox = union_bounding_boxes([t.bbox for t in line])
            results.append((line_text, line_bbox))
        return results
