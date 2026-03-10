from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.domain.entities.enums import BookingStatus


class BookingCreateDTO(BaseModel):
    """Input DTO for creating a new booking."""
    user_id: int
    room_name: Optional[str] = Field(default=None, description="Tên phòng họp (VD: CR7 tầng 2, OKOK tầng 3)")
    reason: str = Field(description="Lý do đặt phòng")
    time: datetime = Field(description="Thời gian đặt phòng (timezone-aware UTC)")
    customer_name: Optional[str] = Field(default=None, description="Tên người đặt")
    customer_phone: Optional[str] = Field(default=None, description="Số điện thoại người đặt")
    note: Optional[str] = Field(default=None, description="Ghi chú thêm")
    email: Optional[str] = Field(default=None, description="Địa chỉ email người đặt")


class BookingUpdateDTO(BaseModel):
    """Input DTO for updating an existing booking."""
    room_name: Optional[str] = Field(default=None)
    reason: Optional[str] = Field(default=None)
    time: Optional[datetime] = Field(default=None)
    customer_name: Optional[str] = Field(default=None)
    customer_phone: Optional[str] = Field(default=None)
    note: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)


class BookingResponseDTO(BaseModel):
    """Output DTO for booking data returned to client."""
    booking_id: int
    user_id: int
    room_name: Optional[str]
    reason: str
    time: datetime
    status: BookingStatus
    customer_name: Optional[str]
    customer_phone: Optional[str]
    note: Optional[str]
    email: Optional[str]

    class Config:
        from_attributes = True


# Backward-compat aliases used by AI tools
BookingData = BookingCreateDTO
BookingResponse = BookingResponseDTO
