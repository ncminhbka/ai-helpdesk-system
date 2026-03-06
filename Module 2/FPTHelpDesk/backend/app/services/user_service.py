"""User CRUD service."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserService:
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        return await UserRepository.get_by_email(db, email)

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        return await UserRepository.get_by_id(db, user_id)

    @staticmethod
    async def create(db: AsyncSession, user_in: UserCreate) -> User:
        return await UserRepository.create(db, user_in)
