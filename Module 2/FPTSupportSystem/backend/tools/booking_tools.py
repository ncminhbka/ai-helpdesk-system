"""
Booking management tools for the Booking Agent.
Supports HITL (Human-in-the-Loop) confirmation before database writes.
"""
from datetime import datetime
from typing import Optional
from langchain_core.tools import tool


@tool
def book_room(
    reason: str,
    time: str,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    note: Optional[str] = None,
    email: Optional[str] = None
) -> dict:
    """
    Prepare a meeting room booking for confirmation.
    This returns data for user confirmation before actual database write.
    
    Args:
        reason: Reason for booking the room (required)
        time: Booking time in format 'YYYY-MM-DD HH:MM' (required)
        customer_name: Booker's name (optional)
        customer_phone: Booker's phone number (optional)
        note: Additional notes (optional)
        email: Booker's email address (optional, may be auto-filled from context)
    
    Returns:
        Dictionary with confirmation data
    """
    return {
        "requires_confirmation": True,
        "action": "create_booking",
        "data": {
            "reason": reason,
            "time": time,
            "customer_name": customer_name or "",
            "customer_phone": customer_phone or "",
            "note": note or "",
            "email": email or "",
        },
        "message_vi": "Vui lòng xác nhận thông tin đặt phòng họp:",
        "message_en": "Please confirm meeting room booking information:",
        "fields": [
            {"name": "reason", "label": "Lý do đặt phòng / Reason", "type": "text", "required": True},
            {"name": "time", "label": "Thời gian / Time", "type": "datetime-local", "required": True},
            {"name": "customer_name", "label": "Họ tên / Name", "type": "text", "required": False},
            {"name": "customer_phone", "label": "Số điện thoại / Phone", "type": "tel", "required": False},
            {"name": "note", "label": "Ghi chú / Note", "type": "textarea", "required": False},
            {"name": "email", "label": "Email", "type": "email", "required": False},
        ]
    }


@tool
def track_booking(booking_id: int) -> dict:
    """
    Track the status and information of an existing booking.
    This is a read-only operation, no confirmation needed.
    
    Args:
        booking_id: The ID of the booking to track
    
    Returns:
        Dictionary indicating this is a query action
    """
    return {
        "requires_confirmation": False,
        "action": "track_booking",
        "data": {
            "booking_id": booking_id
        }
    }


@tool
def update_booking(
    booking_id: int,
    reason: Optional[str] = None,
    time: Optional[str] = None,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    note: Optional[str] = None,
    email: Optional[str] = None
) -> dict:
    """
    Prepare booking update for confirmation.
    Only provided fields will be updated.
    
    Args:
        booking_id: ID of the booking to update (required)
        reason: Updated reason (optional)
        time: Updated time in format 'YYYY-MM-DD HH:MM' (optional)
        customer_name: Updated booker name (optional)
        customer_phone: Updated phone number (optional)
        note: Updated note (optional)
        email: Updated email (optional)
    
    Returns:
        Dictionary with confirmation data
    """
    update_data = {"booking_id": booking_id}
    fields = []
    
    if reason is not None:
        update_data["reason"] = reason
        fields.append({"name": "reason", "label": "Lý do / Reason", "type": "text"})
    
    if time is not None:
        update_data["time"] = time
        fields.append({"name": "time", "label": "Thời gian / Time", "type": "datetime-local"})
    
    if customer_name is not None:
        update_data["customer_name"] = customer_name
        fields.append({"name": "customer_name", "label": "Họ tên / Name", "type": "text"})
    
    if customer_phone is not None:
        update_data["customer_phone"] = customer_phone
        fields.append({"name": "customer_phone", "label": "Số điện thoại / Phone", "type": "tel"})
    
    if note is not None:
        update_data["note"] = note
        fields.append({"name": "note", "label": "Ghi chú / Note", "type": "textarea"})
    
    if email is not None:
        update_data["email"] = email
        fields.append({"name": "email", "label": "Email", "type": "email"})
    
    return {
        "requires_confirmation": True,
        "action": "update_booking",
        "data": update_data,
        "message_vi": f"Vui lòng xác nhận cập nhật đặt phòng #{booking_id}:",
        "message_en": f"Please confirm update for booking #{booking_id}:",
        "fields": fields
    }


@tool
def cancel_booking(booking_id: int) -> dict:
    """
    Prepare booking cancellation for confirmation.
    
    Args:
        booking_id: ID of the booking to cancel
    
    Returns:
        Dictionary with confirmation data
    """
    return {
        "requires_confirmation": True,
        "action": "cancel_booking",
        "data": {
            "booking_id": booking_id
        },
        "message_vi": f"Bạn có chắc muốn hủy đặt phòng #{booking_id}?",
        "message_en": f"Are you sure you want to cancel booking #{booking_id}?",
        "fields": []
    }


# ==================== ACTUAL DATABASE OPERATIONS ====================
# These are called AFTER user confirmation

async def execute_create_booking(db_session, user_id: int, data: dict) -> dict:
    """Execute booking creation after user confirmation."""
    from database import Booking, BookingStatus
    from utils.helpers import parse_datetime
    
    # Parse time string
    booking_time = parse_datetime(data["time"])
    if not booking_time:
        return {
            "success": False,
            "message_vi": "❌ Định dạng thời gian không hợp lệ",
            "message_en": "❌ Invalid time format"
        }
    
    booking = Booking(
        user_id=user_id,
        reason=data["reason"],
        time=booking_time,
        customer_name=data.get("customer_name"),
        customer_phone=data.get("customer_phone"),
        note=data.get("note"),
        email=data.get("email"),
        status=BookingStatus.SCHEDULED.value
    )
    
    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)
    
    return {
        "success": True,
        "booking_id": booking.booking_id,
        "message_vi": f"✅ Đã đặt phòng họp thành công với mã #{booking.booking_id}\n"
                      f"📅 Thời gian: {booking_time.strftime('%d/%m/%Y %H:%M')}",
        "message_en": f"✅ Meeting room booked successfully with ID #{booking.booking_id}\n"
                      f"📅 Time: {booking_time.strftime('%Y-%m-%d %H:%M')}"
    }


async def execute_track_booking(db_session, user_id: int, data: dict) -> dict:
    """Execute booking tracking query."""
    from sqlalchemy import select
    from database import Booking
    
    booking_id = data["booking_id"]
    
    result = await db_session.execute(
        select(Booking).where(
            Booking.booking_id == booking_id,
            Booking.user_id == user_id
        )
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        return {
            "success": False,
            "message_vi": f"❌ Không tìm thấy đặt phòng #{booking_id}",
            "message_en": f"❌ Booking #{booking_id} not found"
        }
    
    return {
        "success": True,
        "booking": booking.to_dict(),
        "message_vi": f"📋 Thông tin đặt phòng #{booking_id}:\n"
                      f"• Lý do: {booking.reason}\n"
                      f"• Thời gian: {booking.time.strftime('%d/%m/%Y %H:%M')}\n"
                      f"• Trạng thái: {booking.status}\n"
                      f"• Ghi chú: {booking.note or 'Không có'}",
        "message_en": f"📋 Booking #{booking_id} information:\n"
                      f"• Reason: {booking.reason}\n"
                      f"• Time: {booking.time.strftime('%Y-%m-%d %H:%M')}\n"
                      f"• Status: {booking.status}\n"
                      f"• Note: {booking.note or 'None'}"
    }


async def execute_update_booking(db_session, user_id: int, data: dict) -> dict:
    """Execute booking update after user confirmation."""
    from sqlalchemy import select
    from database import Booking, BookingStatus
    from utils.helpers import parse_datetime
    
    booking_id = data.pop("booking_id")
    
    result = await db_session.execute(
        select(Booking).where(
            Booking.booking_id == booking_id,
            Booking.user_id == user_id
        )
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        return {
            "success": False,
            "message_vi": f"❌ Không tìm thấy đặt phòng #{booking_id}",
            "message_en": f"❌ Booking #{booking_id} not found"
        }
    
    # Check if booking can be updated
    if booking.status in [BookingStatus.FINISHED.value, BookingStatus.CANCELED.value]:
        return {
            "success": False,
            "message_vi": f"❌ Không thể cập nhật đặt phòng đã {booking.status.lower()}",
            "message_en": f"❌ Cannot update booking with status {booking.status}"
        }
    
    # Update fields
    for key, value in data.items():
        if hasattr(booking, key) and value is not None:
            if key == "time":
                parsed_time = parse_datetime(value)
                if parsed_time:
                    booking.time = parsed_time
            else:
                setattr(booking, key, value)
    
    await db_session.commit()
    
    return {
        "success": True,
        "booking_id": booking_id,
        "message_vi": f"✅ Đã cập nhật đặt phòng #{booking_id} thành công",
        "message_en": f"✅ Booking #{booking_id} updated successfully"
    }


async def execute_cancel_booking(db_session, user_id: int, data: dict) -> dict:
    """Execute booking cancellation after user confirmation."""
    from sqlalchemy import select
    from database import Booking, BookingStatus
    
    booking_id = data["booking_id"]
    
    result = await db_session.execute(
        select(Booking).where(
            Booking.booking_id == booking_id,
            Booking.user_id == user_id
        )
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        return {
            "success": False,
            "message_vi": f"❌ Không tìm thấy đặt phòng #{booking_id}",
            "message_en": f"❌ Booking #{booking_id} not found"
        }
    
    if booking.status == BookingStatus.FINISHED.value:
        return {
            "success": False,
            "message_vi": "❌ Không thể hủy đặt phòng đã hoàn thành",
            "message_en": "❌ Cannot cancel a completed booking"
        }
    
    if booking.status == BookingStatus.CANCELED.value:
        return {
            "success": False,
            "message_vi": "❌ Đặt phòng này đã được hủy trước đó",
            "message_en": "❌ This booking was already canceled"
        }
    
    booking.status = BookingStatus.CANCELED.value
    await db_session.commit()
    
    return {
        "success": True,
        "booking_id": booking_id,
        "message_vi": f"✅ Đã hủy đặt phòng #{booking_id} thành công",
        "message_en": f"✅ Booking #{booking_id} canceled successfully"
    }
