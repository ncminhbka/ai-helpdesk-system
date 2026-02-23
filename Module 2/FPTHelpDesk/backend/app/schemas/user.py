from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None

    class Config:
        from_attributes = True
