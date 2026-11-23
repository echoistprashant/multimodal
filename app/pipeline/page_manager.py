"""Page Image Storage and Thumbnail Management.

Handles persistence of full-resolution rasterized page images and lightweight
thumbnails for fast frontend rendering in review queues.
"""

import io
import uuid
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.page import Page
from app.pipeline.render import RasterizedPage
from app.storage.base import StorageProvider

logger = get_logger("app.pipeline.page_manager")


class PageManager:
    """Manages storage and database persistence for rendered document pages."""

    def __init__(self, session: AsyncSession, storage: StorageProvider) -> None:
        self.session = session
        self.storage = storage

    def _generate_thumbnail(self, image_bytes: bytes, max_width: int = 250) -> bytes:
        """Create a scaled-down thumbnail from high-res image bytes."""
        with Image.open(io.BytesIO(image_bytes)) as img:
            aspect = img.height / img.width
            thumb_height = int(max_width * aspect)
            thumb = img.resize((max_width, thumb_height), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            thumb.save(buf, format="PNG", optimize=True)
            return buf.getvalue()

    async def save_rendered_page(
        self,
        document_id: uuid.UUID,
        tenant_id: str,
        page: RasterizedPage,
    ) -> Page:
        """Store page image, generate thumbnail, and create or update Page entity."""
        # Storage keys
        page_image_key = f"tenants/{tenant_id}/docs/{document_id}/pages/page_{page.page_no}.png"
        thumb_key = f"tenants/{tenant_id}/docs/{document_id}/pages/page_{page.page_no}_thumb.png"

        # 1. Store full resolution image
        await self.storage.put_object(page_image_key, page.image_bytes, "image/png")

        # 2. Store thumbnail
        thumb_bytes = self._generate_thumbnail(page.image_bytes)
        await self.storage.put_object(thumb_key, thumb_bytes, "image/png")

        # 3. Create or update Page database record
        stmt = select(Page).where(
            Page.document_id == document_id,
            Page.page_no == page.page_no,
        )
        result = await self.session.execute(stmt)
        page_entity = result.scalar_one_or_none()

        if not page_entity:
            page_entity = Page(
                id=uuid.uuid4(),
                document_id=document_id,
                page_no=page.page_no,
                width_px=page.width_px,
                height_px=page.height_px,
                dpi=page.dpi,
                image_key=page_image_key,
                rotation=page.rotation,
            )
            self.session.add(page_entity)
        else:
            page_entity.width_px = page.width_px
            page_entity.height_px = page.height_px
            page_entity.dpi = page.dpi
            page_entity.image_key = page_image_key
            page_entity.rotation = page.rotation

        await self.session.flush()
        return page_entity
