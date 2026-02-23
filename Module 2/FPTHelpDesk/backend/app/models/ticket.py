"""Support ticket model with status management."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.models.base import Base


class TicketStatus(str, enum.Enum):
    PENDING = "Pending"
    RESOLVING = "Resolving"
    CANCELED = "Canceled"
    FINISHED = "Finished"


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    customer_name = Column(String(255), nullable=True)
    customer_phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    time = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default=TicketStatus.PENDING.value)

    # Relationships
    user = relationship("User", back_populates="tickets")
