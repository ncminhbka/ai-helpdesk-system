"""
Booking management tools for the Booking Agent.
Supports HITL (Human-in-the-Loop) confirmation before database writes.
"""
from datetime import datetime
from typing import Optional
from langchain_core.tools import tool


@tool
async def book_room(
    reason: str,
    time: str,
    user_id: int,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    note: Optional[str] = None,
    email: Optional[str] = None
) -> dict:
    """
    Book a meeting room.
    
    Args:
        reason: Reason for booking the room (required)
        time: Booking time in format 'YYYY-MM-DD HH:MM' (required)
        user_id: ID of the user booking the room (required)
        customer_name: Booker's name (optional)
        customer_phone: Booker's phone number (optional)
        note: Additional notes (optional)
        email: Booker's email address (optional, may be auto-filled from context)
    
    Returns:
        Dictionary with result message.
    """
    from app.models.booking import Booking, BookingStatus
    from app.utils.helpers import parse_datetime
    from app.core.database import async_session_maker
    
    async with async_session_maker() as db:
        # Parse time string
        booking_time = parse_datetime(time)
        if not booking_time:
            return {
                "success": False,
                "message": "❌ Invalid time format. Please use YYYY-MM-DD HH:MM."
            }
        
        booking = Booking(
            user_id=user_id,
            reason=reason,
            time=booking_time,
            customer_name=customer_name,
            customer_phone=customer_phone,
            note=note,
            email=email,
            status=BookingStatus.SCHEDULED.value
        )
        
        db.add(booking)
        await db.commit()
        await db.refresh(booking)
        
        return {
            "success": True,
            "message": f"✅ Meeting room booked successfully with ID #{booking.booking_id}\n"
                          f"📅 Time: {booking_time.strftime('%Y-%m-%d %H:%M')}"
        }


@tool
async def track_booking(booking_id: int, user_id: int) -> dict:
    """
    Track the status and information of an existing booking.
    
    Args:
        booking_id: The ID of the booking to track
        user_id: The ID of the user
    
    Returns:
        Dictionary with booking info.
    """
    from sqlalchemy import select
    from app.models.booking import Booking
    from app.core.database import async_session_maker
    
    async with async_session_maker() as db:
        result = await db.execute(
            select(Booking).where(
                Booking.booking_id == booking_id,
                Booking.user_id == user_id
            )
        )
        booking = result.scalar_one_or_none()
        
        if not booking:
            return {"success": False, "message": f"❌ Booking #{booking_id} not found"}
        
        return {
            "success": True,
            "message": f"📋 Booking #{booking_id} information:\n"
                          f"• Reason: {booking.reason}\n"
                          f"• Time: {booking.time.strftime('%Y-%m-%d %H:%M')}\n"
                          f"• Status: {booking.status}\n"
                          f"• Note: {booking.note or 'None'}"
        }


@tool
async def update_booking(
    booking_id: int,
    user_id: int,
    reason: Optional[str] = None,
    time: Optional[str] = None,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    note: Optional[str] = None,
    email: Optional[str] = None
) -> dict:
    """
    Update an existing booking.
    
    Args:
        booking_id: ID of the booking to update (required)
        user_id: ID of the user (required)
        reason: Updated reason (optional)
        time: Updated time in format 'YYYY-MM-DD HH:MM' (optional)
        customer_name: Updated booker name (optional)
        customer_phone: Updated phone number (optional)
        note: Updated note (optional)
        email: Updated email (optional)
    
    Returns:
        Dictionary with result message.
    """
    from sqlalchemy import select
    from app.models.booking import Booking, BookingStatus
    from app.utils.helpers import parse_datetime
    from app.core.database import async_session_maker
    
    async with async_session_maker() as db:
        result = await db.execute(
            select(Booking).where(
                Booking.booking_id == booking_id,
                Booking.user_id == user_id
            )
        )
        booking = result.scalar_one_or_none()
        
        if not booking:
            return {"success": False, "message": f"❌ Booking #{booking_id} not found"}
        
        if booking.status in [BookingStatus.FINISHED.value, BookingStatus.CANCELED.value]:
            return {"success": False, "message": f"❌ Cannot update booking with status {booking.status}"}
        
        if reason: booking.reason = reason
        if customer_name: booking.customer_name = customer_name
        if customer_phone: booking.customer_phone = customer_phone
        if note: booking.note = note
        if email: booking.email = email
        if time:
            parsed_time = parse_datetime(time)
            if parsed_time:
                booking.time = parsed_time
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"✅ Booking #{booking_id} updated successfully"
        }


@tool
async def cancel_booking(booking_id: int, user_id: int) -> dict:
    """
    Cancel a booking.
    
    Args:
        booking_id: ID of the booking to cancel
        user_id: ID of the user
    
    Returns:
        Dictionary with result message.
    """
    from sqlalchemy import select
    from app.models.booking import Booking, BookingStatus
    from app.core.database import async_session_maker
    
    async with async_session_maker() as db:
        result = await db.execute(
            select(Booking).where(
                Booking.booking_id == booking_id,
                Booking.user_id == user_id
            )
        )
        booking = result.scalar_one_or_none()
        
        if not booking:
            return {"success": False, "message": f"❌ Booking #{booking_id} not found"}
        
        if booking.status == BookingStatus.FINISHED.value:
            return {"success": False, "message": "❌ Cannot cancel a completed booking"}
        
        if booking.status == BookingStatus.CANCELED.value:
            return {"success": False, "message": "❌ This booking was already canceled"}
        
        booking.status = BookingStatus.CANCELED.value
        await db.commit()
        
        return {
            "success": True,
            "message": f"✅ Booking #{booking_id} canceled successfully"
        }
