"""Ticket domain entity — pure Python, no framework dependencies."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.entities.enums import TicketStatus
from app.domain.exceptions import InvalidTicketStatusError


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

    def assert_can_be_updated(self) -> None:
        if self.status in (TicketStatus.FINISHED, TicketStatus.CANCELED):
            raise InvalidTicketStatusError(
                f"Cannot update ticket #{self.ticket_id}: status is '{self.status.value}'."
            )

    def apply_status(self, status_str: str) -> None:
        valid = [s.value for s in TicketStatus]
        if status_str not in valid:
            raise InvalidTicketStatusError(
                f"Invalid status '{status_str}'. Valid: {', '.join(valid)}"
            )
        self.status = TicketStatus(status_str)
