"""User CRUD use case."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.models.user_model import User
from app.infrastructure.repositories.user_repository import UserRepository
from app.application.dtos.user_dto import UserCreate


class UserUseCase:
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        return await UserRepository.get_by_email(db, email)

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        return await UserRepository.get_by_id(db, user_id)

    @staticmethod
    async def create(db: AsyncSession, user_in: UserCreate) -> User:
        return await UserRepository.create(db, user_in)
