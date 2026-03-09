"""Abstract interface for ticket data access."""
from abc import ABC, abstractmethod
from typing import Optional, List


class ITicketRepository(ABC):
    @abstractmethod
    async def create(
        self, db, user_id: int, content: str, description: str,
        customer_name: Optional[str], customer_phone: Optional[str],
        email: Optional[str]
    ) -> object: ...

    @abstractmethod
    async def get_by_id(self, db, ticket_id: int) -> Optional[object]: ...

    @abstractmethod
    async def get_recent_by_user_id(self, db, user_id: int, limit: int) -> List[object]: ...

    @abstractmethod
    async def update(self, db, ticket: object) -> object: ...
