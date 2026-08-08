"""Projects Workspace REST API Endpoints.

Implements CRUD routes for managing isolated user projects and workspace resources.
"""

import math
import uuid
from fastapi import APIRouter, Depends, Query, status

from src.api.dependencies import get_current_user, get_project_service
from src.application.services.project_service import ProjectService
from src.db.models.user import User
from src.schemas.common import PageMeta, PaginatedResponse
from src.schemas.project import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)

router = APIRouter(prefix="/projects", tags=["Workspace Projects"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Workspace Project",
    description="Creates a new workspace project for the authenticated user.",
)
async def create_project(
    payload: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Creates a new project for current user."""
    project = await project_service.create_project(
        user_id=current_user.id, request=payload
    )
    return ProjectResponse.model_validate(project)


@router.get(
    "",
    response_model=PaginatedResponse[ProjectResponse],
    status_code=status.HTTP_200_OK,
    summary="List User Projects",
    description="Retrieves a paginated list of projects owned by the authenticated user.",
)
async def list_user_projects(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> PaginatedResponse[ProjectResponse]:
    """Lists projects for current user."""
    projects, total_count = await project_service.get_user_projects(
        user_id=current_user.id, page=page, page_size=page_size
    )

    items = [ProjectResponse.model_validate(p) for p in projects]
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0

    return PaginatedResponse[ProjectResponse](
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
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Project Details",
    description="Retrieves details for a specific project owned by the authenticated user.",
)
async def get_project_by_id(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Fetches single project enforcing user ownership."""
    project = await project_service.get_project_by_id(
        project_id=project_id, user_id=current_user.id
    )
    return ProjectResponse.model_validate(project)


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Project Details",
    description="Updates title or description for a project owned by the authenticated user.",
)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdateRequest,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Updates existing project for current user."""
    project = await project_service.update_project(
        project_id=project_id, user_id=current_user.id, request=payload
    )
    return ProjectResponse.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Project",
    description="Deletes a project and all associated crawl jobs/datasets owned by the authenticated user.",
)
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> None:
    """Deletes project for current user."""
    await project_service.delete_project(
        project_id=project_id, user_id=current_user.id
    )
