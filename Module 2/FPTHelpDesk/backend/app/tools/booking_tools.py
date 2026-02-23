"""
Booking tools for the Booking Agent.
Handles meeting room booking, tracking, updating, and cancellation.
"""
from langchain_core.tools import tool
from sqlalchemy import select
from app.core.database import async_session_maker
from app.models.booking import Booking, BookingStatus
from app.utils.helpers import parse_datetime


@tool
async def book_room(
    reason: str,
    time: str,
    room_name: str = None,
    customer_name: str = None,
    customer_phone: str = None,
    note: str = None,
    email: str = None,
    user_id: int = None,
) -> str:
    """
    Book a meeting room.

    Args:
        reason: Purpose of the booking
        time: Booking time (YYYY-MM-DD HH:MM format)
        room_name: Name of the meeting room (e.g. CR7 tầng 2, OKOK tầng 3)
        customer_name: Name of the person booking (optional)
        customer_phone: Phone number (optional)
        note: Additional notes (optional)
        email: Contact email (optional)
        user_id: User ID from context (injected automatically)
    """
    parsed_time = parse_datetime(time)
    if not parsed_time:
        return f"❌ Invalid time format: '{time}'. Please use YYYY-MM-DD HH:MM format."

    async with async_session_maker() as session:
        booking = Booking(
            user_id=user_id or 0,
            room_name=room_name,
            customer_name=customer_name,
            customer_phone=customer_phone,
            email=email,
            reason=reason,
            time=parsed_time,
            note=note,
            status=BookingStatus.SCHEDULED.value,
        )
        session.add(booking)
        await session.commit()
        await session.refresh(booking)

        return (
            f"✅ Room booked successfully!\n"
            f"📋 Booking ID: {booking.booking_id}\n"
            f"🏢 Room: {room_name or 'N/A'}\n"
            f"📝 Reason: {reason}\n"
            f"📅 Time: {parsed_time.strftime('%Y-%m-%d %H:%M')}\n"
            f"👤 Name: {customer_name or 'N/A'}\n"
            f"📧 Email: {email or 'N/A'}\n"
            f"📌 Status: {booking.status}"
        )


@tool
async def track_booking(
    booking_id: int = None,
    user_id: int = None,
) -> str:
    """
    Track booking status. Provide booking_id for specific booking,
    or leave empty to see all bookings for the current user.

    Args:
        booking_id: Specific booking ID to track (optional)
        user_id: User ID from context (injected automatically)
    """
    async with async_session_maker() as session:
        if booking_id:
            result = await session.execute(
                select(Booking).where(Booking.booking_id == booking_id)
            )
            booking = result.scalar_one_or_none()
            if not booking:
                return f"❌ Booking #{booking_id} not found."
            return _format_booking(booking)
        else:
            result = await session.execute(
                select(Booking)
                .where(Booking.user_id == (user_id or 0))
                .order_by(Booking.time.desc())
                .limit(10)
            )
            bookings = result.scalars().all()
            if not bookings:
                return "📋 No bookings found."
            return "\n\n---\n\n".join(_format_booking(b) for b in bookings)


@tool
async def update_booking(
    booking_id: int,
    room_name: str = None,
    reason: str = None,
    time: str = None,
    customer_name: str = None,
    customer_phone: str = None,
    note: str = None,
    email: str = None,
) -> str:
    """
    Update an existing booking. Only non-Finished and non-Canceled bookings can be updated.

    Args:
        booking_id: ID of the booking to update
        room_name: Updated room name (optional)
        reason: Updated reason (optional)
        time: Updated time in YYYY-MM-DD HH:MM format (optional)
        customer_name: Updated name (optional)
        customer_phone: Updated phone (optional)
        note: Updated note (optional)
        email: Updated email (optional)
    """
    async with async_session_maker() as session:
        result = await session.execute(
            select(Booking).where(Booking.booking_id == booking_id)
        )
        booking = result.scalar_one_or_none()

        if not booking:
            return f"❌ Booking #{booking_id} not found."

        if booking.status in [BookingStatus.FINISHED.value, BookingStatus.CANCELED.value]:
            return f"❌ Cannot update booking #{booking_id}: status is '{booking.status}'."

        updates = []
        if room_name:
            booking.room_name = room_name
            updates.append(f"Room → {room_name}")
        if reason:
            booking.reason = reason
            updates.append(f"Reason → {reason}")
        if time:
            parsed_time = parse_datetime(time)
            if not parsed_time:
                return f"❌ Invalid time format: '{time}'."
            booking.time = parsed_time
            updates.append(f"Time → {parsed_time.strftime('%Y-%m-%d %H:%M')}")
        if customer_name:
            booking.customer_name = customer_name
            updates.append(f"Name → {customer_name}")
        if customer_phone:
            booking.customer_phone = customer_phone
            updates.append(f"Phone → {customer_phone}")
        if note:
            booking.note = note
            updates.append(f"Note → {note}")
        if email:
            booking.email = email
            updates.append(f"Email → {email}")

        if not updates:
            return "⚠️ No fields to update."

        await session.commit()
        return f"✅ Booking #{booking_id} updated:\n" + "\n".join(f"  • {u}" for u in updates)


@tool
async def cancel_booking(booking_id: int) -> str:
    """
    Cancel an existing booking. Only non-Finished bookings can be canceled.

    Args:
        booking_id: ID of the booking to cancel
    """
    async with async_session_maker() as session:
        result = await session.execute(
            select(Booking).where(Booking.booking_id == booking_id)
        )
        booking = result.scalar_one_or_none()

        if not booking:
            return f"❌ Booking #{booking_id} not found."

        if booking.status == BookingStatus.FINISHED.value:
            return f"❌ Cannot cancel booking #{booking_id}: already Finished."

        if booking.status == BookingStatus.CANCELED.value:
            return f"⚠️ Booking #{booking_id} is already Canceled."

        booking.status = BookingStatus.CANCELED.value
        await session.commit()
        return f"✅ Booking #{booking_id} has been canceled."


def _format_booking(booking: Booking) -> str:
    """Format a booking for display."""
    time_str = booking.time.strftime("%Y-%m-%d %H:%M") if booking.time else "N/A"
    return (
        f"📅 Booking #{booking.booking_id}\n"
        f"  🏢 Room: {booking.room_name or 'N/A'}\n"
        f"  📝 Reason: {booking.reason}\n"
        f"  🕒 Time: {time_str}\n"
        f"  👤 Name: {booking.customer_name or 'N/A'}\n"
        f"  📞 Phone: {booking.customer_phone or 'N/A'}\n"
        f"  📧 Email: {booking.email or 'N/A'}\n"
        f"  📌 Status: {booking.status}"
    )
