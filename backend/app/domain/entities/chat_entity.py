"""Chat domain entities — pure Python, no framework dependencies."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ChatSessionEntity:
    session_id: str
    user_id: int
    title: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class MessageEntity:
    id: Optional[int]
    session_id: str
    role: str
    content: str
    message_type: str = "message" 
    metadata: Optional[dict] = field(default=None)
    created_at: Optional[datetime] = None
