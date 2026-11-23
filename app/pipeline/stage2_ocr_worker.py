"""Stage 2 Pipeline Worker: Image Preprocessing and OCR Execution.

Orchestrates visual preprocessing (denoise, deskew, binarize), OCR engine execution,
token spatial extraction, and persistence into relational layout blocks.
"""

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.page import Page
from app.ocr import get_ocr_engine
from app.ocr.persistence import OCRPersistenceHandler
from app.preprocess import apply_gaussian_denoise, binarize_document, convert_to_grayscale
from app.storage.base import StorageProvider

logger = get_logger("app.pipeline.stage2")


class Stage2OCRWorker:
    """Worker processing scanned pages requiring OCR text recognition."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageProvider,
    ) -> None:
        self.session = session
        self.storage = storage
        self.settings = get_settings()
        self.ocr_engine = get_ocr_engine(self.settings.OCR_ENGINE)
        self.persistence = OCRPersistenceHandler(session)

    async def process_document_ocr(
        self,
        document_id: uuid.UUID,
    ) -> int:
        """Run preprocessing and OCR across all OCR-routed pages for a document."""
        stmt = (
            select(Page)
            .where(Page.document_id == document_id, Page.route == "ocr")
            .order_by(Page.page_no)
        )
        result = await self.session.execute(stmt)
        pages = result.scalars().all()

        total_processed = 0

        for page in pages:
            if not page.image_key:
                logger.warning(f"Page {page.page_no} has no image key, skipping OCR")
                continue

            # 1. Fetch page image bytes from storage
            raw_image = await self.storage.get_object(page.image_key)

            # 2. Apply preprocessing pipeline
            gray = convert_to_grayscale(raw_image)
            denoised = apply_gaussian_denoise(gray, radius=0.8)
            cleaned_image = binarize_document(denoised, autocontrast=True)

            # 3. Execute OCR engine
            tokens = await self.ocr_engine.extract_tokens(cleaned_image, page_no=page.page_no)

            # 4. Check confidence threshold for VLM escalation
            if tokens:
                mean_conf = sum(t.confidence for t in tokens) / len(tokens)
                if mean_conf < 0.60:
                    logger.info(
                        f"Page {page.page_no} low OCR confidence ({mean_conf:.2f} < 0.60). Escalating to VLM fallback."
                    )
                    page.route = "vlm"

            # 5. Persist tokens into blocks
            await self.persistence.persist_page_tokens(page=page, tokens=tokens)
            total_processed += 1

        await self.session.commit()
        logger.info(f"Stage 2 OCR completed for doc {document_id}: {total_processed} pages processed")
        return total_processed
