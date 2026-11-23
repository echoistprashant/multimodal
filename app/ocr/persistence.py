"""OCR Results Relational Persistence Module.

Persists grouped OCR text lines and normalized spatial coordinates into the
database as Block entities linked to the corresponding Page.
"""

import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.block import Block
from app.models.page import Page
from app.ocr.aggregator import TokenAggregator
from app.parser.schema import Token

logger = get_logger("app.ocr.persistence")


class OCRPersistenceHandler:
    """Handles persisting OCR results into database relational blocks."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.aggregator = TokenAggregator()

    async def persist_page_tokens(
        self,
        page: Page,
        tokens: Sequence[Token],
    ) -> list[Block]:
        """Aggregate tokens into lines and insert Block records."""
        if not tokens:
            return []

        lines = self.aggregator.group_tokens_into_lines(tokens)
        serialized = self.aggregator.serialize_lines_to_text(lines)

        blocks: list[Block] = []
        for idx, (line_text, bbox) in enumerate(serialized):
            block = Block(
                id=uuid.uuid4(),
                page_id=page.id,
                type="text",
                reading_order=idx,
                x0=bbox.x0,
                y0=bbox.y0,
                x1=bbox.x1,
                y1=bbox.y1,
                text=line_text,
                content={"source": "ocr", "token_count": len(line_text.split())},
            )
            self.session.add(block)
            blocks.append(block)

        # Compute average confidence across tokens as page quality score
        avg_confidence = round(sum(t.confidence for t in tokens) / len(tokens), 3)
        page.quality_score = avg_confidence
        page.route = "ocr"

        await self.session.flush()
        logger.info(
            f"Persisted {len(blocks)} OCR blocks for page {page.page_no} (quality={avg_confidence})"
        )
        return blocks
