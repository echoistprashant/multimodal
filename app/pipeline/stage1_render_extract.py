"""Stage 1 Pipeline Worker: Rendering and Native Digital Text Extraction.

Coordinates PDF rasterization, page image storage, and native digital text parsing.
Determines whether each page proceeds to native processing or requires OCR fallback.
"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.block import Block
from app.parser.native import NativePDFParser
from app.pipeline.page_manager import PageManager
from app.pipeline.render import PDFRasterizer
from app.repositories.document_repo import DocumentRepository
from app.storage.base import StorageProvider

logger = get_logger("app.pipeline.stage1")


class Stage1Worker:
    """Orchestrates document rasterization and native text extraction."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageProvider,
        dpi: int = 200,
    ) -> None:
        self.session = session
        self.storage = storage
        self.rasterizer = PDFRasterizer(dpi=dpi)
        self.page_manager = PageManager(session, storage)
        self.native_parser = NativePDFParser()
        self.doc_repo = DocumentRepository(session)

    async def process_document(
        self,
        document_id: uuid.UUID,
        tenant_id: str,
    ) -> int:
        """Execute Stage 1 for the document. Returns total pages rendered."""
        doc = await self.doc_repo.get_by_id(document_id, tenant_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        # 1. Fetch raw document bytes from storage
        pdf_bytes = await self.storage.get_object(doc.storage_key)

        # 2. Rasterize pages
        rendered_pages = self.rasterizer.render_all_pages(pdf_bytes)
        page_count = len(rendered_pages)

        # 3. Process each page: store image and extract native text if present
        for rp in rendered_pages:
            page_entity = await self.page_manager.save_rendered_page(
                document_id=doc.id,
                tenant_id=tenant_id,
                page=rp,
            )

            # Attempt native digital text extraction
            parse_result = self.native_parser.parse_page(pdf_bytes, rp.page_no)
            if parse_result.has_text_layer and parse_result.tokens:
                page_entity.route = "native"
                # Save initial text blocks
                for idx, token in enumerate(parse_result.tokens):
                    block = Block(
                        id=uuid.uuid4(),
                        page_id=page_entity.id,
                        type="text",
                        reading_order=idx,
                        x0=token.bbox.x0,
                        y0=token.bbox.y0,
                        x1=token.bbox.x1,
                        y1=token.bbox.y1,
                        text=token.text,
                        content={"source": "native", "confidence": token.confidence},
                    )
                    self.session.add(block)
            else:
                # Needs OCR in Stage 2
                page_entity.route = "ocr"

        # 4. Update document state
        await self.doc_repo.update_status(
            document_id=doc.id,
            tenant_id=tenant_id,
            status="processing",
            page_count=page_count,
        )
        await self.session.commit()

        logger.info(
            f"Stage 1 completed for doc {doc.id}: {page_count} pages rasterized and triaged",
            extra={"document_id": str(doc.id), "tenant_id": tenant_id},
        )
        return page_count
