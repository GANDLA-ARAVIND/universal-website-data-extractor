"""ProjectService Use-Case Layer.

Manages user projects, workspace isolation, and project CRUD operations.
"""

import uuid
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import BaseAppException
from src.db.models.project import Project
from src.db.repositories.project_repository import ProjectRepository
from src.schemas.project import ProjectCreateRequest, ProjectUpdateRequest


class ProjectNotFoundException(BaseAppException):
    """Raised when a requested project does not exist or does not belong to the user."""

    pass


class ProjectService:
    """Service layer managing workspace project CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.project_repo = ProjectRepository(session)

    async def create_project(
        self, user_id: uuid.UUID, request: ProjectCreateRequest
    ) -> Project:
        """Creates a new workspace project for an authenticated user."""
        return await self.project_repo.create_project(
            user_id=user_id,
            name=request.name,
            description=request.description,
        )

    async def get_user_projects(
        self, user_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> Tuple[List[Project], int]:
        """Retrieves paginated workspace projects for an authenticated user."""
        return await self.project_repo.get_user_projects(
            user_id=user_id, page=page, page_size=page_size
        )

    async def get_project_by_id(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> Project:
        """Fetches project by ID enforcing owner user authorization."""
        project = await self.project_repo.get_by_id(project_id, user_id=user_id)
        if not project:
            raise ProjectNotFoundException(f"Project with ID '{project_id}' was not found.")
        return project

    async def update_project(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        request: ProjectUpdateRequest,
    ) -> Project:
        """Updates project details for an authorized owner user."""
        project = await self.project_repo.update_project(
            project_id=project_id,
            user_id=user_id,
            name=request.name,
            description=request.description,
        )
        if not project:
            raise ProjectNotFoundException(f"Project with ID '{project_id}' was not found.")
        return project

    async def delete_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        """Deletes a project owned by an authorized user."""
        deleted = await self.project_repo.delete_project(
            project_id=project_id, user_id=user_id
        )
        if not deleted:
            raise ProjectNotFoundException(f"Project with ID '{project_id}' was not found.")
        return True
