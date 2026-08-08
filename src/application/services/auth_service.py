"""AuthService Use-Case Layer.

Manages user registration, password verification, authentication, and JWT issuance.
"""

import uuid
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import BaseAppException
from src.core.security import create_access_token, hash_password, verify_password
from src.db.models.user import User
from src.db.repositories.user_repository import UserRepository
from src.schemas.auth import UserLoginRequest, UserRegisterRequest


class InvalidCredentialsException(BaseAppException):
    """Raised when authentication credentials (email/password) are invalid."""

    pass


class UserAlreadyExistsException(BaseAppException):
    """Raised when attempting to register an email address that already exists."""

    pass


class AuthService:
    """Service handling user registration, authentication, and JWT lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)

    async def register_user(self, request: UserRegisterRequest) -> User:
        """Registers a new user after verifying email uniqueness."""
        existing = await self.user_repo.get_by_email(request.email)
        if existing:
            raise UserAlreadyExistsException(f"User with email '{request.email}' already exists.")

        hashed_pwd = hash_password(request.password)
        return await self.user_repo.create_user(
            email=request.email,
            password_hash=hashed_pwd,
        )

    async def authenticate_user(self, request: UserLoginRequest) -> Tuple[User, str]:
        """Authenticates user credentials and returns (User, jwt_token)."""
        user = await self.user_repo.get_by_email(request.email)
        if not user or not verify_password(request.password, user.password_hash):
            raise InvalidCredentialsException("Invalid email or password.")

        if not user.is_active:
            raise InvalidCredentialsException("User account is inactive.")

        token = create_access_token(subject=str(user.id))
        return user, token

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Retrieves user by primary key UUID."""
        return await self.user_repo.get_by_id(user_id)
