"""Ticket domain entity — pure Python, no framework dependencies."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.entities.enums import TicketStatus


@dataclass
class TicketEntity:
    ticket_id: Optional[int]
    user_id: int
    content: str
    description: str
    status: TicketStatus
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    email: Optional[str] = None
    time: Optional[datetime] = None  # timezone-aware UTC
