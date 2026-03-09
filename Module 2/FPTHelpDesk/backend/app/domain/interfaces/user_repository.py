"""Abstract interface for user data access."""
from abc import ABC, abstractmethod
from typing import Optional


class IUserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, db, email: str) -> Optional[object]: ...

    @abstractmethod
    async def get_by_id(self, db, user_id: int) -> Optional[object]: ...

    @abstractmethod
    async def create(self, db, user_in) -> object: ...
