from typing import Optional
from pydantic import BaseModel, Field


class TicketResponse(BaseModel):
    """Schema phản hồi thông tin Ticket hỗ trợ."""
    ticket_id: int
    content: str               # Tiêu đề hoặc nội dung vắn tắt
    description: Optional[str] # Mô tả chi tiết vấn đề
    customer_name: Optional[str]
    customer_phone: Optional[str]
    email: Optional[str]
    time: Optional[str]
    status: str                # Trạng thái Ticket (VD: Mở, Đang xử lý, Đã đóng)

    class Config:
        from_attributes = True


class TicketData(BaseModel):
    """Schema dữ liệu đầu vào để tạo một Ticket mới thông qua AI Agent."""
    content: str = Field(description="Mô tả ngắn gọn về vấn đề cần hỗ trợ")
    description: str = Field(description="Mô tả chi tiết nội dung lỗi hoặc yêu cầu")
    customer_name: Optional[str] = Field(default=None, description="Tên khách hàng")
    customer_phone: Optional[str] = Field(default=None, description="Số điện thoại liên hệ")
    email: Optional[str] = Field(default=None, description="Địa chỉ email liên hệ")


class TicketUpdateData(BaseModel):
    """Schema dữ liệu dùng để cập nhật thông tin một Ticket đã tồn tại."""
    ticket_id: int = Field(description="ID của Ticket cần cập nhật")
    content: Optional[str] = Field(default=None, description="Cập nhật nội dung vắn tắt")
    description: Optional[str] = Field(default=None, description="Cập nhật mô tả chi tiết")
    customer_name: Optional[str] = Field(default=None, description="Cập nhật tên khách hàng")
    customer_phone: Optional[str] = Field(default=None, description="Cập nhật số điện thoại")
    email: Optional[str] = Field(default=None, description="Cập nhật địa chỉ email")
