"""
Database configuration and SQLAlchemy models for FPT Customer Support Chatbot.
"""
import os
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import enum

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./fpt_chatbot.db")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

Base = declarative_base()


# ==================== ENUMS ====================

class TicketStatus(str, enum.Enum):
    PENDING = "Pending"
    RESOLVING = "Resolving"
    CANCELED = "Canceled"
    FINISHED = "Finished"


class BookingStatus(str, enum.Enum):
    SCHEDULED = "Scheduled"
    CANCELED = "Canceled"
    FINISHED = "Finished"


# ==================== MODELS ====================

class User(Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="user", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")


class ChatSession(Base):
    """Chat session for conversation management."""
    __tablename__ = "chat_sessions"
    
    session_id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    """Message model for storing chat history."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("chat_sessions.session_id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="message")  # 'message', 'confirm', 'error'
    metadata_json = Column(Text, nullable=True)  # JSON string for extra data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")


class Ticket(Base):
    """Support ticket model."""
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
    
    def to_dict(self) -> dict:
        return {
            "ticket_id": self.ticket_id,
            "content": self.content,
            "description": self.description,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "email": self.email,
            "time": self.time.isoformat() if self.time else None,
            "status": self.status
        }


class Booking(Base):
    """Room booking model."""
    __tablename__ = "bookings"
    
    booking_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    customer_name = Column(String(255), nullable=True)
    customer_phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    reason = Column(String(500), nullable=False)
    time = Column(DateTime, nullable=False)
    note = Column(Text, nullable=True)
    status = Column(String(20), default=BookingStatus.SCHEDULED.value)
    
    # Relationships
    user = relationship("User", back_populates="bookings")
    
    def to_dict(self) -> dict:
        return {
            "booking_id": self.booking_id,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "email": self.email,
            "reason": self.reason,
            "time": self.time.isoformat() if self.time else None,
            "note": self.note,
            "status": self.status
        }


class PendingAction(Base):
    """Pending HITL actions awaiting user confirmation."""
    __tablename__ = "pending_actions"
    
    action_id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(36), nullable=False)
    action_type = Column(String(50), nullable=False)  # 'create_ticket', 'create_booking', etc.
    data_json = Column(Text, nullable=False)  # JSON string with action data
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)


# ==================== DATABASE FUNCTIONS ====================

async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized successfully")


async def get_db():
    """Dependency for getting database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email."""
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID."""
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, password_hash: str, name: str = None) -> User:
    """Create new user."""
    user = User(email=email, password_hash=password_hash, name=name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# Run initialization if executed directly
if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
