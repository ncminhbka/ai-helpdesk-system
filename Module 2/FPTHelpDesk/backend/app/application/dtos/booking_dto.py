from typing import Optional
from pydantic import BaseModel, Field


class BookingResponse(BaseModel):
    """Schema cho phản hồi thông tin đặt phòng."""
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
    """Schema mô tả dữ liệu cần thiết cho công cụ đặt phòng (book_room tool)."""
    room_name: Optional[str] = Field(default=None, description="Tên phòng họp (VD: CR7 tầng 2, OKOK tầng 3)")
    reason: str = Field(description="Lý do đặt phòng")
    time: str = Field(description="Thời gian đặt phòng định dạng YYYY-MM-DD HH:MM")
    customer_name: Optional[str] = Field(default=None, description="Tên người đặt")
    customer_phone: Optional[str] = Field(default=None, description="Số điện thoại người đặt")
    note: Optional[str] = Field(default=None, description="Ghi chú thêm")
    email: Optional[str] = Field(default=None, description="Địa chỉ email người đặt")
