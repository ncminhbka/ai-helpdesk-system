"""User domain entity — pure Python, no framework dependencies."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class UserEntity:
    id: Optional[int]
    email: str
    password_hash: str
    name: str
    created_at: Optional[datetime] = None
