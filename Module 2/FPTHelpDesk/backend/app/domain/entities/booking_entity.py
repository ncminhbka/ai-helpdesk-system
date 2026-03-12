"""Booking domain entity — pure Python, no framework dependencies."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.entities.enums import BookingStatus
from app.domain.exceptions import InvalidBookingStatusError


@dataclass
class BookingEntity:
    booking_id: Optional[int]
    user_id: int
    room_name: str
    reason: str
    time: datetime  # timezone-aware UTC
    status: BookingStatus
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    note: Optional[str] = None
    email: Optional[str] = None

    def assert_can_be_updated(self) -> None:
        if self.status in (BookingStatus.FINISHED, BookingStatus.CANCELED):
            raise InvalidBookingStatusError(
                f"Cannot update booking #{self.booking_id}: status is '{self.status.value}'."
            )

    def cancel(self) -> None:
        if self.status == BookingStatus.FINISHED:
            raise InvalidBookingStatusError(
                f"Cannot cancel booking #{self.booking_id}: already Finished."
            )
        if self.status == BookingStatus.CANCELED:
            raise InvalidBookingStatusError(
                f"Booking #{self.booking_id} is already Canceled."
            )
        self.status = BookingStatus.CANCELED
