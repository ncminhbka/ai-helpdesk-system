"""Meeting room booking model with status management."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.models.base import Base


class BookingStatus(str, enum.Enum):
    SCHEDULED = "Scheduled"
    CANCELED = "Canceled"
    FINISHED = "Finished"


class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # khoá ngoại trỏ đến bảng users
    room_name = Column(String(255), nullable=True)
    customer_name = Column(String(255), nullable=True)
    customer_phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    reason = Column(String(500), nullable=False)
    time = Column(DateTime(timezone=True), nullable=False)
    note = Column(Text, nullable=True)
    status = Column(String(20), default=BookingStatus.SCHEDULED.value)

    # Relationships
    user = relationship("User", back_populates="bookings") # 1 user có nhiều booking
