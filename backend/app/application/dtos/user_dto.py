from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    """Schema chứa các thông tin cần thiết khi tạo tài khoản người dùng mới."""
    email: str
    password: str
    name: Optional[str] = None


class UserResponse(BaseModel):
    """Schema chứa thông tin người dùng gửi về cho client (không bao gồm mật khẩu)."""
    id: int
    email: str
    name: Optional[str] = None

    class Config:
        from_attributes = True
