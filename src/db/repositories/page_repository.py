"""PageRepository Database Access Object.

Encapsulates persistence operations for extracted web pages, hyperlinks, and image assets.
"""

import uuid
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.crawler.extractors.html_extractor import ExtractedContentDTO
from src.db.models.image import PageImage
from src.db.models.link import PageLink
from src.db.models.page import ExtractedPage
from src.utils.url_utils import normalize_url


class PageRepository:
    """Repository handling ExtractedPage, PageLink, and PageImage database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_extracted_page(
        self,
        job_id: uuid.UUID,
        dto: ExtractedContentDTO,
        depth: int,
        status_code: int,
        response_time_ms: float,
    ) -> ExtractedPage:
        """Persists extracted page content, headings, paragraphs, links, and images.

        Args:
            job_id (uuid.UUID): Crawl job primary key.
            dto (ExtractedContentDTO): Parsed feature DTO.
            depth (int): Traversal depth.
            status_code (int): HTTP status code.
            response_time_ms (float): Fetch latency ms.

        Returns:
            ExtractedPage: Created ORM instance.
        """
        page = ExtractedPage(
            job_id=job_id,
            url=dto.url,
            normalized_url=normalize_url(dto.url),
            status_code=status_code,
            depth=depth,
            title=dto.title,
            meta_description=dto.meta_description,
            headings=dto.headings,
            paragraphs=dto.paragraphs,
            lists=dto.lists,
            tables=dto.tables,
            response_time_ms=response_time_ms,
        )
        self.session.add(page)
        await self.session.flush()  # Flush to generate page.id for foreign keys

        # Batch insert extracted images
        for img_dict in dto.images:
            page_image = PageImage(
                page_id=page.id,
                image_url=img_dict["image_url"],
                alt_text=img_dict.get("alt_text"),
            )
            self.session.add(page_image)

        # Batch insert extracted links
        all_links = dto.internal_links + dto.external_links
        for link_dict in all_links:
            page_link = PageLink(
                page_id=page.id,
                source_url=link_dict["source_url"],
                target_url=link_dict["target_url"],
                anchor_text=link_dict.get("anchor_text"),
                is_external=link_dict["is_external"],
            )
            self.session.add(page_link)

        await self.session.commit()
        await self.session.refresh(page)
        return page


    async def get_pages_by_job_id(
        self,
        job_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[ExtractedPage], int]:
        """Retrieves paginated extracted pages for a crawl job.

        Args:
            job_id (uuid.UUID): Job UUID.
            skip (int): Pagination offset.
            limit (int): Max records per page.

        Returns:
            Tuple[List[ExtractedPage], int]: (Extracted pages list, Total pages count).
        """
        count_stmt = select(func.count(ExtractedPage.id)).where(
            ExtractedPage.job_id == job_id
        )
        total_count = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            select(ExtractedPage)
            .options(
                selectinload(ExtractedPage.links),
                selectinload(ExtractedPage.images),
            )
            .where(ExtractedPage.job_id == job_id)
            .order_by(ExtractedPage.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        pages = list(result.scalars().all())
        return pages, total_count

    async def get_all_pages_for_job(
        self, job_id: uuid.UUID
    ) -> List[ExtractedPage]:
        """Retrieves all extracted pages for a job (used for file exports)."""
        stmt = (
            select(ExtractedPage)
            .options(
                selectinload(ExtractedPage.links),
                selectinload(ExtractedPage.images),
            )
            .where(ExtractedPage.job_id == job_id)
            .order_by(ExtractedPage.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
