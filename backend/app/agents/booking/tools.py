"""
Booking tools for the Booking Agent.
Handles meeting room booking, tracking, updating, and cancellation.
"""
from typing import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app.models.booking import Booking
from app.services.booking_service import BookingService
from app.utils.hitl import hitl_protected


# ==================== TOOLS ====================

@tool
@hitl_protected(display_name="Đặt phòng họp", cancel_message="❌ Người dùng đã hủy thao tác đặt phòng.")
async def book_room(
    reason: str,
    time: str,
    room_name: str = None,
    customer_name: str = None,
    customer_phone: str = None,
    note: str = None,
    email: str = None,
    user_id: Annotated[int, InjectedState("user_id")] = None,
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
    """
    if not user_id:
        return "❌ Lỗi: Không thể xác định người dùng. Vui lòng đăng nhập lại."

    try:
        booking = await BookingService.create_booking(
            user_id=user_id,
            room_name=room_name,
            reason=reason,
            time_str=time,
            customer_name=customer_name,
            customer_phone=customer_phone,
            email=email,
            note=note,
        )
        return (
            f"✅ Room booked successfully!\n"
            f"📋 Booking ID: {booking.booking_id}\n"
            f"🏢 Room: {room_name or 'N/A'}\n"
            f"📝 Reason: {reason}\n"
            f"📅 Time: {booking.time.strftime('%Y-%m-%d %H:%M')}\n"
            f"👤 Name: {customer_name or 'N/A'}\n"
            f"📧 Email: {email or 'N/A'}\n"
            f"📌 Status: {booking.status}"
        )
    except ValueError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


@tool
async def track_booking(
    booking_id: int = None,
    user_id: Annotated[int, InjectedState("user_id")] = None,
) -> str:
    """
    Track booking status. Provide booking_id for specific booking,
    or leave empty to see all bookings for the current user.

    Args:
        booking_id: Specific booking ID to track (optional)
    """
    if booking_id:
        booking = await BookingService.get_booking_by_id(booking_id)
        if not booking:
            return f"❌ Booking #{booking_id} not found."
        return _format_booking(booking)
    else:
        if not user_id:
            return "❌ Lỗi: Không thể xác định người dùng. Vui lòng đăng nhập lại."
        bookings = await BookingService.get_recent_bookings_by_user(user_id)
        if not bookings:
            return "📋 No bookings found."
        return "\n\n---\n\n".join(_format_booking(b) for b in bookings)


@tool
@hitl_protected(display_name="Cập nhật đặt phòng", cancel_message="❌ Người dùng đã hủy thao tác cập nhật đặt phòng.")
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
    success, message, updates = await BookingService.update_booking(
        booking_id=booking_id,
        room_name=room_name,
        reason=reason,
        time_str=time,
        customer_name=customer_name,
        customer_phone=customer_phone,
        note=note,
        email=email,
    )
    
    if not success:
        return message
        
    return f"{message}\n" + "\n".join(f"  • {u}" for u in updates)


@tool
@hitl_protected(display_name="Hủy đặt phòng", cancel_message="❌ Người dùng đã hủy thao tác hủy đặt phòng.")
async def cancel_booking(booking_id: int) -> str:
    """
    Cancel an existing booking. Only non-Finished bookings can be canceled.

    Args:
        booking_id: ID of the booking to cancel
    """
    success, message = await BookingService.cancel_booking(booking_id)
    return message


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
