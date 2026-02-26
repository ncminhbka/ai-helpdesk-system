from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Schema cho yêu cầu chat từ phía người dùng."""
    session_id: str  # ID của phiên làm việc
    message: str     # Nội dung tin nhắn người dùng gửi


class ChatResponse(BaseModel):
    """Schema cho phản hồi từ hệ thống chat."""
    type: str  # Loại phản hồi: 'message' (tin nhắn thường), 'confirm' (xác nhận hành động), 'error' (lỗi)
    content: Optional[str] = None # Nội dung phản hồi
    action: Optional[str] = None  # Tên tool cần xác nhận (chỉ khi type='confirm')
    data: Optional[Dict[str, Any]] = None  # Args của tool (chỉ khi type='confirm')


class SessionCreate(BaseModel):
    """Schema để tạo một phiên chat mới."""
    title: Optional[str] = "New Chat" # Tiêu đề phiên chat


class SessionUpdate(BaseModel):
    """Schema để cập nhật thông tin phiên chat."""
    title: str # Tiêu đề mới cho phiên chat


class SessionResponse(BaseModel):
    """Schema mô tả thông tin chi tiết của một phiên chat trả về cho client."""
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Schema mô tả thông tin một tin nhắn trong lịch sử chat."""
    role: str           # Vai trò: 'user' hoặc 'assistant'
    content: str        # nội dung tin nhắn
    message_type: str   # Loại tin nhắn (text, tool_call, v.v.)
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None # Các dữ liệu bổ sung đính kèm

    class Config:
        from_attributes = True
