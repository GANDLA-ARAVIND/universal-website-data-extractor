"""Authentication REST API Endpoints.

Handles registration, login credentials verification, HTTP-only JWT cookie setting,
logout session clearing, and current user identity retrieval.
"""

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse

from src.api.dependencies import get_auth_service, get_current_user
from src.application.services.auth_service import AuthService
from src.core.config import settings
from src.db.models.user import User
from src.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User Account",
    description="Registers a new user account with unique email address and hashed password.",
)
async def register_user(
    payload: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Registers a new user."""
    user = await auth_service.register_user(payload)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticates credentials, returns signed JWT access token, and sets secure HTTP-only cookie.",
)
async def login_user(
    payload: UserLoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticates user and attaches HTTP-only access_token cookie."""
    user, token = await auth_service.authenticate_user(payload)

    # Set secure HTTP-only cookie
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )

    user_resp = UserResponse.model_validate(user)
    return TokenResponse(access_token=token, token_type="bearer", user=user_resp)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="User Logout",
    description="Clears the HTTP-only authentication cookie.",
)
async def logout_user(response: Response) -> dict:
    """Deletes authentication cookie."""
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite="lax",
    )
    return {"message": "Successfully logged out."}


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile",
    description="Retrieves authenticated user profile information.",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Returns current active user entity."""
    return UserResponse.model_validate(current_user)
