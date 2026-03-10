from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.domain.entities.enums import TicketStatus


class TicketCreateDTO(BaseModel):
    """Input DTO for creating a new ticket."""
    user_id: int
    content: str = Field(description="Mô tả ngắn gọn về vấn đề cần hỗ trợ")
    description: str = Field(description="Mô tả chi tiết nội dung lỗi hoặc yêu cầu")
    customer_name: Optional[str] = Field(default=None, description="Tên khách hàng")
    customer_phone: Optional[str] = Field(default=None, description="Số điện thoại liên hệ")
    email: Optional[str] = Field(default=None, description="Địa chỉ email liên hệ")


class TicketUpdateDTO(BaseModel):
    """Input DTO for updating an existing ticket."""
    content: Optional[str] = Field(default=None, description="Cập nhật nội dung vắn tắt")
    description: Optional[str] = Field(default=None, description="Cập nhật mô tả chi tiết")
    status: Optional[str] = Field(default=None, description="Cập nhật trạng thái ticket")
    customer_name: Optional[str] = Field(default=None, description="Cập nhật tên khách hàng")
    customer_phone: Optional[str] = Field(default=None, description="Cập nhật số điện thoại")
    email: Optional[str] = Field(default=None, description="Cập nhật địa chỉ email")


class TicketResponseDTO(BaseModel):
    """Output DTO for ticket data returned to client."""
    ticket_id: int
    user_id: int
    content: str
    description: Optional[str]
    status: TicketStatus
    customer_name: Optional[str]
    customer_phone: Optional[str]
    email: Optional[str]
    time: Optional[datetime]

    class Config:
        from_attributes = True


# Backward-compat aliases used by AI tools
TicketData = TicketCreateDTO
TicketUpdateData = TicketUpdateDTO
TicketResponse = TicketResponseDTO
