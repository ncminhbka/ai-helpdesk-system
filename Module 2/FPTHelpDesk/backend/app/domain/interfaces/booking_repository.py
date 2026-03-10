"""Abstract interface for booking data access."""
from abc import ABC, abstractmethod
from typing import Optional, List

from app.domain.entities.booking_entity import BookingEntity


class IBookingRepository(ABC):
    @abstractmethod
    async def create(self, booking: BookingEntity) -> BookingEntity: ...

    @abstractmethod
    async def get_by_id(self, booking_id: int) -> Optional[BookingEntity]: ...

    @abstractmethod
    async def get_recent_by_user_id(self, user_id: int, limit: int = 10) -> List[BookingEntity]: ...

    @abstractmethod
    async def update(self, booking: BookingEntity) -> BookingEntity: ...
