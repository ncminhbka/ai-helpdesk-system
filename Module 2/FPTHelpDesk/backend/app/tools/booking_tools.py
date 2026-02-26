"""
Booking tools for the Booking Agent.
Handles meeting room booking, tracking, updating, and cancellation.
Uses dynamic interrupt() for HITL confirmation on sensitive operations.
"""
from langchain_core.tools import tool
from sqlalchemy import select
from langgraph.types import interrupt

from app.core.database import async_session_maker
from app.core.config import settings
from app.models.booking import Booking, BookingStatus
from app.utils.helpers import parse_datetime


# ==================== HITL HELPERS ====================

# Fields that should not be shown to the user in confirmation
_HIDDEN_FIELDS = {"user_id", "session_id"}

# Vietnamese labels for display
_FIELD_LABELS = {
    "room_name": "Phòng", "reason": "Lý do", "time": "Thời gian",
    "customer_name": "Tên KH", "customer_phone": "SĐT",
    "email": "Email", "note": "Ghi chú",
    "booking_id": "Mã đặt phòng", "status": "Trạng thái",
}

_ACTION_LABELS = {
    "book_room": "Đặt phòng họp",
    "update_booking": "Cập nhật đặt phòng",
    "cancel_booking": "Hủy đặt phòng",
}

# HITL gate shows args to user and let them confirm, then return edited args or None if rejected before writing to database
def _hitl_gate(tool_name: str, args: dict) -> dict | None:
    """
    HITL gate using dynamic interrupt().
    Returns the (possibly edited) args if approved, or None if rejected.
    Only activates when ENABLE_HITL is True.
    """
    if not settings.ENABLE_HITL:
        return args

    # Build visible args (filter out hidden fields and None values)
    visible_args = {
        k: v for k, v in args.items()
        if k not in _HIDDEN_FIELDS and v is not None
    }

    response = interrupt({
        "action": tool_name,
        "display_name": _ACTION_LABELS.get(tool_name, tool_name),
        "args": visible_args,
        "field_labels": {k: v for k, v in _FIELD_LABELS.items() if k in visible_args},
    })

    if isinstance(response, dict) and response.get("action") == "approve":
        # Apply user edits if any (user args override tool args)
        edits = response.get("edits", {})
        merged = {**args}
        for key, value in edits.items():
            if key in merged and value is not None and str(value).strip():
                merged[key] = value
        return merged

    # Rejected or unrecognized response
    return None


# ==================== TOOLS ====================

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
    # HITL gate — may pause here for user confirmation
    args = _hitl_gate("book_room", {
        "reason": reason, "time": time, "room_name": room_name,
        "customer_name": customer_name, "customer_phone": customer_phone,
        "note": note, "email": email, "user_id": user_id,
    })
    if args is None:
        return "❌ Người dùng đã hủy thao tác đặt phòng."

    # Unpack (possibly edited) args
    reason = args["reason"]
    time = args["time"]
    room_name = args.get("room_name")
    customer_name = args.get("customer_name")
    customer_phone = args.get("customer_phone")
    note = args.get("note")
    email = args.get("email")
    user_id = args.get("user_id")

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
    # HITL gate
    args = _hitl_gate("update_booking", {
        "booking_id": booking_id, "room_name": room_name, "reason": reason,
        "time": time, "customer_name": customer_name,
        "customer_phone": customer_phone, "note": note, "email": email,
    })
    if args is None:
        return "❌ Người dùng đã hủy thao tác cập nhật đặt phòng."

    # Unpack (possibly edited) args
    booking_id = args["booking_id"]
    room_name = args.get("room_name")
    reason = args.get("reason")
    time = args.get("time")
    customer_name = args.get("customer_name")
    customer_phone = args.get("customer_phone")
    note = args.get("note")
    email = args.get("email")

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
    # HITL gate
    args = _hitl_gate("cancel_booking", {"booking_id": booking_id})
    if args is None:
        return "❌ Người dùng đã hủy thao tác hủy đặt phòng."

    booking_id = args["booking_id"]

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
