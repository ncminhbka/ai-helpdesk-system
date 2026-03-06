from typing import List, Optional
from datetime import datetime

from app.core.database import async_session_maker
from app.models.booking import Booking, BookingStatus
from app.repositories.booking_repository import BookingRepository
from app.utils.helpers import parse_datetime


class BookingService:

    @staticmethod
    async def create_booking(
        user_id: int,
        room_name: Optional[str],
        reason: str,
        time_str: str,
        customer_name: Optional[str] = None,
        customer_phone: Optional[str] = None,
        email: Optional[str] = None,
        note: Optional[str] = None,
    ) -> Booking:
        parsed_time = parse_datetime(time_str)
        if not parsed_time:
            raise ValueError(f"Invalid time format: '{time_str}'. Please use YYYY-MM-DD HH:MM format.")

        async with async_session_maker() as session:
            booking = await BookingRepository.create(
                db=session,
                user_id=user_id,
                room_name=room_name,
                customer_name=customer_name,
                customer_phone=customer_phone,
                email=email,
                reason=reason,
                time=parsed_time,
                note=note,
            )
            return booking

    @staticmethod
    async def get_booking_by_id(booking_id: int) -> Optional[Booking]:
        async with async_session_maker() as session:
            return await BookingRepository.get_by_id(session, booking_id)

    @staticmethod
    async def get_recent_bookings_by_user(user_id: int, limit: int = 10) -> List[Booking]:
        async with async_session_maker() as session:
            return await BookingRepository.get_recent_by_user_id(session, user_id, limit)

    @staticmethod
    async def update_booking(
        booking_id: int,
        room_name: Optional[str] = None,
        reason: Optional[str] = None,
        time_str: Optional[str] = None,
        customer_name: Optional[str] = None,
        customer_phone: Optional[str] = None,
        note: Optional[str] = None,
        email: Optional[str] = None,
    ) -> tuple[bool, str, List[str]]:
        """Returns (success, message, list_of_updates)."""
        async with async_session_maker() as session:
            booking = await BookingRepository.get_by_id(session, booking_id)

            if not booking:
                return False, f"❌ Booking #{booking_id} not found.", []

            if booking.status in [BookingStatus.FINISHED.value, BookingStatus.CANCELED.value]:
                return False, f"❌ Cannot update booking #{booking_id}: status is '{booking.status}'.", []

            updates = []
            if room_name:
                booking.room_name = room_name
                updates.append(f"Room → {room_name}")
            if reason:
                booking.reason = reason
                updates.append(f"Reason → {reason}")
            if time_str:
                parsed_time = parse_datetime(time_str)
                if not parsed_time:
                    return False, f"❌ Invalid time format: '{time_str}'.", []
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
                return False, "⚠️ No fields to update.", []

            await BookingRepository.update(session, booking)
            return True, f"✅ Booking #{booking_id} updated.", updates

    @staticmethod
    async def cancel_booking(booking_id: int) -> tuple[bool, str]:
        """Returns (success, message)."""
        async with async_session_maker() as session:
            booking = await BookingRepository.get_by_id(session, booking_id)

            if not booking:
                return False, f"❌ Booking #{booking_id} not found."

            if booking.status == BookingStatus.FINISHED.value:
                return False, f"❌ Cannot cancel booking #{booking_id}: already Finished."

            if booking.status == BookingStatus.CANCELED.value:
                return False, f"⚠️ Booking #{booking_id} is already Canceled."

            booking.status = BookingStatus.CANCELED.value
            await BookingRepository.update(session, booking)
            return True, f"✅ Booking #{booking_id} has been canceled."

