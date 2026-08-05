"""ORMs model package initialization."""

from src.db.models.crawl_job import CrawlJob, CrawlStatus
from src.db.models.page import ExtractedPage
from src.db.models.link import PageLink
from src.db.models.image import PageImage
from src.db.models.statistic import CrawlStatistic

__all__ = [
    "CrawlJob",
    "CrawlStatus",
    "ExtractedPage",
    "PageLink",
    "PageImage",
    "CrawlStatistic",
]
