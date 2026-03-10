"""Abstract interface for user data access."""
from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.user_entity import UserEntity


class IUserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[UserEntity]: ...

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[UserEntity]: ...

    @abstractmethod
    async def create(self, user: UserEntity) -> UserEntity: ...
