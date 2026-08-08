"""ProjectRepository Database Access Object."""

import uuid
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.project import Project


class ProjectRepository:
    """Repository handling Project ORM database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_project(
        self,
        user_id: uuid.UUID,
        name: str,
        description: Optional[str] = None,
    ) -> Project:
        """Creates and persists a new user Project."""
        project = Project(
            user_id=user_id,
            name=name.strip(),
            description=description.strip() if description else None,
        )
        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def get_user_projects(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Project], int]:
        """Retrieves paginated projects owned by a user."""
        count_stmt = select(func.count(Project.id)).where(Project.user_id == user_id)
        total_count = (await self.session.execute(count_stmt)).scalar_one() or 0

        offset = (page - 1) * page_size
        stmt = (
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        res = await self.session.execute(stmt)
        projects = list(res.scalars().all())
        return projects, total_count

    async def get_by_id(
        self,
        project_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
    ) -> Optional[Project]:
        """Fetches Project by ID, optionally enforcing user ownership."""
        stmt = select(Project).where(Project.id == project_id)
        if user_id:
            stmt = stmt.where(Project.user_id == user_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def update_project(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Project]:
        """Updates project details for an owner."""
        project = await self.get_by_id(project_id, user_id=user_id)
        if not project:
            return None

        if name is not None:
            project.name = name.strip()
        if description is not None:
            project.description = description.strip()

        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def delete_project(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Deletes a project owned by a user."""
        project = await self.get_by_id(project_id, user_id=user_id)
        if not project:
            return False

        await self.session.delete(project)
        await self.session.commit()
        return True
