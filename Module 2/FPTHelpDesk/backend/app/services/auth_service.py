"""Authentication service."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.services.user_service import UserService
from app.core.security import verify_password


class AuthService:
    @staticmethod
    async def authenticate(db: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await UserService.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
