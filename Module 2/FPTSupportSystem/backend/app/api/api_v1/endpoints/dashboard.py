
from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User
from app.models.ticket import Ticket
from app.models.booking import Booking
from app.schemas.ticket import TicketResponse
from app.schemas.booking import BookingResponse
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/tickets", response_model=List[TicketResponse])
async def list_tickets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """List all tickets for current user."""
    result = await db.execute(
        select(Ticket)
        .where(Ticket.user_id == current_user.id)
        .order_by(Ticket.time.desc())
    )
    tickets = result.scalars().all()
    
    # Manually map if needed, but Pydantic should handle if fields match
    # Since Ticket model has 'time' and Schema has 'time' as datetime, it should work.
    # The original code did manual string conversion but Pydantic handles datetime.
    return tickets

@router.get("/bookings", response_model=List[BookingResponse])
async def list_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """List all bookings for current user."""
    result = await db.execute(
        select(Booking)
        .where(Booking.user_id == current_user.id)
        .order_by(Booking.time.desc())
    )
    bookings = result.scalars().all()
    return bookings
