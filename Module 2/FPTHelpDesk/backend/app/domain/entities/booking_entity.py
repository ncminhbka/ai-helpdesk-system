"""Booking domain entity — pure Python, no framework dependencies."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.entities.enums import BookingStatus


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
