from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user_entity import UserEntity
from app.domain.interfaces.user_repository import IUserRepository
from app.infrastructure.database.models.user_model import User


class UserRepository(IUserRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_entity(self, model: User) -> UserEntity:
        return UserEntity(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            name=model.name,
            created_at=model.created_at,
        )

    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        result = await self.db.execute(select(User).where(User.email == email))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_id(self, user_id: int) -> Optional[UserEntity]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, user: UserEntity) -> UserEntity:
        db_user = User(
            email=user.email,
            password_hash=user.password_hash,
            name=user.name,
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return self._to_entity(db_user)
