"""
Booking tools for the Booking Agent.
Handles meeting room booking, tracking, updating, and cancellation.
"""
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app.application.dtos.booking_dto import BookingCreateDTO, BookingResponseDTO, BookingUpdateDTO
from app.application.use_cases.booking_use_case import BookingUseCase
from app.infrastructure.utils.helpers import parse_datetime
from app.domain.exceptions import BookingNotFoundError, InvalidBookingStatusError
from app.infrastructure.database.engine import async_session_maker
from app.infrastructure.ai.hitl.decorator import hitl_protected
from app.infrastructure.repositories.booking_repository import BookingRepository


def _get_use_case(db) -> BookingUseCase:
    return BookingUseCase(BookingRepository(db))


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

    parsed_time = parse_datetime(time)
    if not parsed_time:
        return f"❌ Invalid time format: '{time}'. Please use YYYY-MM-DD HH:MM format."

    try:
        async with async_session_maker() as db:
            use_case = _get_use_case(db)
            booking = await use_case.create_booking(
                BookingCreateDTO(
                    user_id=user_id,
                    room_name=room_name,
                    reason=reason,
                    time=parsed_time,
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    note=note,
                    email=email,
                )
            )
        return (
            f"✅ Room booked successfully!\n"
            f"📋 Booking ID: {booking.booking_id}\n"
            f"🏢 Room: {room_name or 'N/A'}\n"
            f"📝 Reason: {reason}\n"
            f"📅 Time: {booking.time.strftime('%Y-%m-%d %H:%M')}\n"
            f"👤 Name: {customer_name or 'N/A'}\n"
            f"📧 Email: {email or 'N/A'}\n"
            f"📌 Status: {booking.status.value}"
        )
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
    async with async_session_maker() as db:
        use_case = _get_use_case(db)
        if booking_id:
            booking = await use_case.get_booking_by_id(booking_id)
            if not booking:
                return f"❌ Booking #{booking_id} not found."
            return _format_booking(booking)
        else:
            if not user_id:
                return "❌ Lỗi: Không thể xác định người dùng. Vui lòng đăng nhập lại."
            bookings = await use_case.get_recent_bookings_by_user(user_id)
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
    parsed_time = None
    if time:
        parsed_time = parse_datetime(time)
        if not parsed_time:
            return f"❌ Invalid time format: '{time}'. Please use YYYY-MM-DD HH:MM format."

    try:
        async with async_session_maker() as db:
            use_case = _get_use_case(db)
            booking = await use_case.update_booking(
                booking_id=booking_id,
                data=BookingUpdateDTO(
                    room_name=room_name,
                    reason=reason,
                    time=parsed_time,
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    note=note,
                    email=email,
                ),
            )
        return f"✅ Booking #{booking.booking_id} updated.\n{_format_booking(booking)}"
    except BookingNotFoundError as e:
        return f"❌ {str(e)}"
    except InvalidBookingStatusError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


@tool
@hitl_protected(display_name="Hủy đặt phòng", cancel_message="❌ Người dùng đã hủy thao tác hủy đặt phòng.")
async def cancel_booking(booking_id: int) -> str:
    """
    Cancel an existing booking. Only non-Finished bookings can be canceled.

    Args:
        booking_id: ID of the booking to cancel
    """
    try:
        async with async_session_maker() as db:
            use_case = _get_use_case(db)
            booking = await use_case.cancel_booking(booking_id)
        return f"✅ Booking #{booking.booking_id} has been canceled."
    except BookingNotFoundError as e:
        return f"❌ {str(e)}"
    except InvalidBookingStatusError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


def _format_booking(booking: BookingResponseDTO) -> str:
    """Format a booking DTO for display."""
    time_str = booking.time.strftime("%Y-%m-%d %H:%M") if booking.time else "N/A"
    return (
        f"📅 Booking #{booking.booking_id}\n"
        f"  🏢 Room: {booking.room_name or 'N/A'}\n"
        f"  📝 Reason: {booking.reason}\n"
        f"  🕒 Time: {time_str}\n"
        f"  👤 Name: {booking.customer_name or 'N/A'}\n"
        f"  📞 Phone: {booking.customer_phone or 'N/A'}\n"
        f"  📧 Email: {booking.email or 'N/A'}\n"
        f"  📌 Status: {booking.status.value}"
    )
