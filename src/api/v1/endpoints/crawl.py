"""Crawl & Export REST API Endpoints.

Implements HTTP routes for initiating crawls, checking statuses, retrieving results,
fetching statistics, and downloading exported datasets.
"""

import uuid
import math
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response, status
from fastapi.responses import StreamingResponse

from src.api.dependencies import (
    get_crawl_service,
    get_current_user_optional,
    get_export_service,
)
from src.application.services.crawl_service import CrawlService
from src.application.services.export_service import ExportService
from src.db.models.crawl_job import CrawlMode, CrawlStatus
from src.db.models.user import User
from src.schemas.common import PageMeta, PaginatedResponse
from src.schemas.crawl import (
    CrawlCreateRequest,
    CrawlJobResponse,
    CrawlStatisticResponse,
)
from src.schemas.export import ExportRequest
from src.schemas.page import ExtractedPageResponse, PaginatedPageResultsResponse

router = APIRouter(prefix="/crawl", tags=["Crawl Operations"])


@router.post(
    "",
    response_model=CrawlJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate Web Crawl Job",
    description="Accepts target seed URL and parameters to start an asynchronous web crawl in the background.",
)
async def initiate_crawl(
    payload: CrawlCreateRequest,
    background_tasks: BackgroundTasks,
    crawl_service: CrawlService = Depends(get_crawl_service),
) -> CrawlJobResponse:
    """Dispatches background web crawl job."""
    job = await crawl_service.initiate_crawl(
        request=payload, background_tasks=background_tasks
    )
    return CrawlJobResponse.model_validate(job)


@router.get(
    "/jobs",
    response_model=PaginatedResponse[CrawlJobResponse],
    status_code=status.HTTP_200_OK,
    summary="List Historical Crawl Jobs",
    description="Retrieves a paginated list of historical crawl jobs with status filtering, seed URL search, and sorting.",
)
async def list_crawl_jobs(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[CrawlStatus] = Query(default=None, alias="status", description="Filter by job status"),
    crawl_mode: Optional[CrawlMode] = Query(default=None, description="Filter by crawl mode (SINGLE/BATCH)"),
    search: Optional[str] = Query(default=None, description="Search by seed URL substring"),
    sort_by: str = Query(default="created_at", description="Field to sort by"),
    sort_order: str = Query(default="desc", description="Sort direction (asc/desc)"),
    crawl_service: CrawlService = Depends(get_crawl_service),
) -> PaginatedResponse[CrawlJobResponse]:
    """Fetches paginated list of crawl jobs history."""
    jobs, total_count = await crawl_service.list_jobs(
        page=page,
        page_size=page_size,
        status=status_filter,
        crawl_mode=crawl_mode,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    items = [CrawlJobResponse.model_validate(j) for j in jobs]
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0

    return PaginatedResponse[CrawlJobResponse](
        data=items,
        meta=PageMeta(
            page=page,
            page_size=page_size,
            total=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        ),
    )


@router.get(
    "/{job_id}",
    response_model=CrawlJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Crawl Job Status",
    description="Retrieves current status and metadata of a crawl job by UUID.",
)
async def get_crawl_status(
    job_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    crawl_service: CrawlService = Depends(get_crawl_service),
) -> CrawlJobResponse:
    """Fetches job status."""
    job = await crawl_service.get_job_status(job_id, current_user=current_user)
    return CrawlJobResponse.model_validate(job)


@router.get(
    "/{job_id}/results",
    response_model=PaginatedPageResultsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Extracted Pages Data",
    description="Retrieves paginated extracted web page content for a crawl job.",
)
async def get_crawl_results(
    job_id: uuid.UUID,
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    crawl_service: CrawlService = Depends(get_crawl_service),
) -> PaginatedPageResultsResponse:
    """Fetches extracted page records."""
    pages, total_count = await crawl_service.get_job_results(
        job_id=job_id, page=page, limit=limit, current_user=current_user
    )

    page_responses = []
    for p in pages:
        res = ExtractedPageResponse(
            id=p.id,
            job_id=p.job_id,
            url=p.url,
            normalized_url=p.normalized_url,
            status_code=p.status_code,
            depth=p.depth,
            title=p.title,
            meta_description=p.meta_description,
            headings=p.headings or {},
            paragraphs=p.paragraphs or [],
            lists=p.lists or [],
            tables=p.tables or [],
            response_time_ms=p.response_time_ms,
            created_at=p.created_at,
            links_count=len(p.links),
            images_count=len(p.images),
        )
        page_responses.append(res)

    total_pages = math.ceil(total_count / limit) if total_count > 0 else 0
    meta = PageMeta(
        page=page,
        page_size=limit,
        total=total_count,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )

    return PaginatedPageResultsResponse(
        total=total_count,
        page=page,
        limit=limit,
        data=page_responses,
        meta=meta,
    )


@router.get(
    "/{job_id}/statistics",
    response_model=CrawlStatisticResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Crawl Statistics",
    description="Retrieves execution metrics (pages count, failed pages, duration) for a crawl job.",
)
async def get_crawl_statistics(
    job_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    crawl_service: CrawlService = Depends(get_crawl_service),
) -> CrawlStatisticResponse:
    """Fetches job execution metrics."""
    stats = await crawl_service.get_job_statistics(job_id, current_user=current_user)
    return CrawlStatisticResponse.model_validate(stats)


from src.schemas.dataset import StandardCrawlDataset


@router.get(
    "/{job_id}/dataset",
    response_model=StandardCrawlDataset,
    status_code=status.HTTP_200_OK,
    summary="Get Standardized Crawl Dataset",
    description="Retrieves the unified StandardCrawlDataset for a crawl job.",
)
async def get_crawl_dataset(
    job_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    crawl_service: CrawlService = Depends(get_crawl_service),
) -> StandardCrawlDataset:
    """Fetches unified crawl dataset container."""
    await crawl_service.get_job_status(job_id, current_user=current_user)
    return await crawl_service.get_job_dataset(job_id)


@router.post(
    "/{job_id}/export",
    summary="Export Extracted Results",
    description="Generates downloadable export file in JSON, CSV, or Markdown format.",
)
async def export_crawl_results(
    job_id: uuid.UUID,
    payload: ExportRequest,
    export_service: ExportService = Depends(get_export_service),
) -> Response:
    """Exports extracted page dataset as downloadable file."""
    file_bytes, filename, media_type = await export_service.generate_export(
        job_id=job_id, export_format=payload.format
    )

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    return Response(content=file_bytes, media_type=media_type, headers=headers)

