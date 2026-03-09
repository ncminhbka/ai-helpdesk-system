"""Authentication use case."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.models.user_model import User
from app.application.use_cases.user_use_case import UserUseCase
from app.infrastructure.security.jwt_bcrypt import verify_password


class AuthUseCase:
    @staticmethod
    async def authenticate(db: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await UserUseCase.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
