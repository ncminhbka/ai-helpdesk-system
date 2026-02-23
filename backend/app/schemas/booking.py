from typing import Optional
from pydantic import BaseModel, Field


class BookingResponse(BaseModel):
    booking_id: int
    room_name: Optional[str]
    customer_name: Optional[str]
    customer_phone: Optional[str]
    email: Optional[str]
    reason: str
    time: Optional[str]
    note: Optional[str]
    status: str

    class Config:
        from_attributes = True


class BookingData(BaseModel):
    """Schema for book_room tool arguments."""
    room_name: Optional[str] = Field(default=None, description="Name of the meeting room (e.g. CR7 tầng 2, OKOK tầng 3)")
    reason: str = Field(description="Reason for booking the room")
    time: str = Field(description="Booking time in YYYY-MM-DD HH:MM format")
    customer_name: Optional[str] = Field(default=None, description="Booker's name")
    customer_phone: Optional[str] = Field(default=None, description="Booker's phone number")
    note: Optional[str] = Field(default=None, description="Additional notes")
    email: Optional[str] = Field(default=None, description="Booker's email address")