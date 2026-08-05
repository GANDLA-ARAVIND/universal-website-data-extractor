"""Crawl & Export REST API Endpoints.

Implements HTTP routes for initiating crawls, checking statuses, retrieving results,
fetching statistics, and downloading exported datasets.
"""

import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response, status
from fastapi.responses import StreamingResponse

from src.api.dependencies import get_crawl_service, get_export_service
from src.application.services.crawl_service import CrawlService
from src.application.services.export_service import ExportService
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
    "/{job_id}",
    response_model=CrawlJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Crawl Job Status",
    description="Retrieves current status and metadata of a crawl job by UUID.",
)
async def get_crawl_status(
    job_id: uuid.UUID,
    crawl_service: CrawlService = Depends(get_crawl_service),
) -> CrawlJobResponse:
    """Fetches job status."""
    job = await crawl_service.get_job_status(job_id)
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
    crawl_service: CrawlService = Depends(get_crawl_service),
) -> PaginatedPageResultsResponse:
    """Fetches extracted page records."""
    pages, total_count = await crawl_service.get_job_results(
        job_id=job_id, page=page, limit=limit
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

    return PaginatedPageResultsResponse(
        total=total_count,
        page=page,
        limit=limit,
        data=page_responses,
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
    crawl_service: CrawlService = Depends(get_crawl_service),
) -> CrawlStatisticResponse:
    """Fetches job execution metrics."""
    stats = await crawl_service.get_job_statistics(job_id)
    return CrawlStatisticResponse.model_validate(stats)


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
