"""Abstract interface for booking data access."""
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime


class IBookingRepository(ABC):
    @abstractmethod
    async def create(
        self, db, user_id: int, room_name: Optional[str],
        customer_name: Optional[str], customer_phone: Optional[str],
        email: Optional[str], reason: str, time: datetime,
        note: Optional[str]
    ) -> object: ...

    @abstractmethod
    async def get_by_id(self, db, booking_id: int) -> Optional[object]: ...

    @abstractmethod
    async def get_recent_by_user_id(self, db, user_id: int, limit: int) -> List[object]: ...

    @abstractmethod
    async def update(self, db, booking: object) -> object: ...
