"""Batch Crawling REST API Endpoints.

Implements HTTP routes for initiating batch crawls, checking status, fetching aggregated metrics,
retrying failed website jobs, and downloading unified multi-website exported datasets.
"""

import uuid
import math
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response, status

from src.api.dependencies import (
    get_batch_service,
    get_current_user_optional,
    get_export_service,
)
from src.application.services.batch_service import BatchService
from src.application.services.export_service import ExportService
from src.db.models.crawl_job import CrawlStatus
from src.db.models.user import User
from src.schemas.batch import (
    BatchCreateRequest,
    BatchJobResponse,
    BatchStatisticResponse,
)
from src.schemas.common import PageMeta, PaginatedResponse
from src.schemas.export import ExportRequest

router = APIRouter(prefix="/batch", tags=["Batch Crawl Operations"])


@router.post(
    "",
    response_model=BatchJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate Multi-Website Batch Crawl",
    description="Accepts a list of target website seed URLs and parameters to execute a batch crawl.",
)
async def initiate_batch_crawl(
    payload: BatchCreateRequest,
    background_tasks: BackgroundTasks,
    batch_service: BatchService = Depends(get_batch_service),
) -> BatchJobResponse:
    """Dispatches background batch crawl job."""
    return await batch_service.initiate_batch_crawl(
        request=payload, background_tasks=background_tasks
    )


@router.get(
    "/list",
    response_model=PaginatedResponse[BatchJobResponse],
    status_code=status.HTTP_200_OK,
    summary="List Batch Crawl Jobs",
    description="Retrieves a paginated list of multi-website batch crawl executions with filtering and sorting.",
)
async def list_batch_jobs(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[CrawlStatus] = Query(default=None, alias="status", description="Filter by batch status"),
    sort_by: str = Query(default="created_at", description="Field to sort by"),
    sort_order: str = Query(default="desc", description="Sort direction (asc/desc)"),
    batch_service: BatchService = Depends(get_batch_service),
) -> PaginatedResponse[BatchJobResponse]:
    """Fetches paginated list of batch crawl executions."""
    batches, total_count = await batch_service.list_batches(
        page=page,
        page_size=page_size,
        status=status_filter,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0

    return PaginatedResponse[BatchJobResponse](
        data=batches,
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
    "/{batch_id}",
    response_model=BatchJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Batch Crawl Status",
    description="Retrieves overall progress, status, and individual child job statuses for a batch.",
)
async def get_batch_status(
    batch_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    batch_service: BatchService = Depends(get_batch_service),
) -> BatchJobResponse:
    """Fetches batch execution progress."""
    return await batch_service.get_batch_status(batch_id, current_user=current_user)


@router.get(
    "/{batch_id}/statistics",
    response_model=BatchStatisticResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Aggregated Batch Statistics",
    description="Retrieves aggregated metrics (total websites, completed, failed, total pages/links/images) for a batch.",
)
async def get_batch_statistics(
    batch_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    batch_service: BatchService = Depends(get_batch_service),
) -> BatchStatisticResponse:
    """Fetches aggregated batch metrics."""
    return await batch_service.get_batch_statistics(batch_id, current_user=current_user)


@router.post(
    "/{batch_id}/retry",
    response_model=BatchJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Retry Failed Websites in Batch",
    description="Re-triggers crawl execution ONLY for child website jobs within a batch that previously failed.",
)
async def retry_failed_websites(
    batch_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_current_user_optional),
    batch_service: BatchService = Depends(get_batch_service),
) -> BatchJobResponse:
    """Re-dispatches failed website crawl jobs."""
    return await batch_service.retry_failed_websites(
        batch_id=batch_id, background_tasks=background_tasks, current_user=current_user
    )


from src.schemas.dataset import BatchDataset


@router.get(
    "/{batch_id}/dataset",
    response_model=BatchDataset,
    status_code=status.HTTP_200_OK,
    summary="Get Multi-Website Batch Dataset",
    description="Retrieves the unified BatchDataset containing independent StandardCrawlDataset items per website.",
)
async def get_batch_dataset(
    batch_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    batch_service: BatchService = Depends(get_batch_service),
    export_service: ExportService = Depends(get_export_service),
) -> BatchDataset:
    """Fetches multi-website batch dataset container."""
    await batch_service.get_batch_status(batch_id, current_user=current_user)
    return await export_service.get_batch_dataset(batch_id)


@router.post(
    "/{batch_id}/export",
    summary="Export Batch Extracted Results",
    description="Generates a downloadable multi-website export file in JSON, CSV, Markdown, PDF, DOCX, or XLSX format.",
)
async def export_batch_results(
    batch_id: uuid.UUID,
    payload: ExportRequest,
    export_service: ExportService = Depends(get_export_service),
) -> Response:
    """Exports batch extracted page dataset as downloadable file."""
    file_bytes, filename, media_type = await export_service.generate_batch_export(
        batch_id=batch_id, export_format=payload.format
    )

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    return Response(content=file_bytes, media_type=media_type, headers=headers)

