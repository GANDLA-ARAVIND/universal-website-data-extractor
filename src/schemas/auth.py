"""Auth Pydantic Schemas for Registration, Login, and Identity."""

import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """Payload schema for user registration."""

    email: EmailStr = Field(
        ...,
        description="User email address.",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Plaintext password (minimum 8 characters).",
        examples=["SecurePass123!"],
    )


class UserLoginRequest(BaseModel):
    """Payload schema for user login authentication."""

    email: EmailStr = Field(
        ...,
        description="User email address.",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        description="User password.",
        examples=["SecurePass123!"],
    )


class UserResponse(BaseModel):
    """Public user identity response schema."""

    id: uuid.UUID
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT Access Token response payload."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
