from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.models.user_model import User
from app.infrastructure.security.jwt_bcrypt import get_password_hash
from app.application.dtos.user_dto import UserCreate
from app.domain.interfaces.user_repository import IUserRepository


class UserRepository(IUserRepository):
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user_in: UserCreate) -> User:
        user = User(
            email=user_in.email,
            password_hash=get_password_hash(user_in.password),
            name=user_in.name,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
