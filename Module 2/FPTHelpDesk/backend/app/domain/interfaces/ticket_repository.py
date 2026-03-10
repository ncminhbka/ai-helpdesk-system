"""Abstract interface for ticket data access."""
from abc import ABC, abstractmethod
from typing import Optional, List

from app.domain.entities.ticket_entity import TicketEntity


class ITicketRepository(ABC):
    @abstractmethod
    async def create(self, ticket: TicketEntity) -> TicketEntity: ...

    @abstractmethod
    async def get_by_id(self, ticket_id: int) -> Optional[TicketEntity]: ...

    @abstractmethod
    async def get_recent_by_user_id(self, user_id: int, limit: int = 10) -> List[TicketEntity]: ...

    @abstractmethod
    async def update(self, ticket: TicketEntity) -> TicketEntity: ...
