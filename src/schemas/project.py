"""Project Pydantic Schemas for CRUD Operations."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    """Payload schema for creating a project."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Project title/name.",
        examples=["Marketing Competitor Intelligence"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Optional project description or notes.",
        examples=["Tracks pricing and feature changes across key SaaS vendors."],
    )


class ProjectUpdateRequest(BaseModel):
    """Payload schema for updating a project."""

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated project title.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Updated project description.",
    )


class ProjectResponse(BaseModel):
    """API response schema for a user project."""

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
