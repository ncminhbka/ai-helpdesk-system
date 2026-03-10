from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.booking_entity import BookingEntity
from app.domain.entities.enums import BookingStatus
from app.domain.interfaces.booking_repository import IBookingRepository
from app.infrastructure.database.models.booking_model import Booking


class BookingRepository(IBookingRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_entity(self, model: Booking) -> BookingEntity:
        return BookingEntity(
            booking_id=model.booking_id,
            user_id=model.user_id,
            room_name=model.room_name,
            reason=model.reason,
            time=model.time,
            status=BookingStatus(model.status),
            customer_name=model.customer_name,
            customer_phone=model.customer_phone,
            note=model.note,
            email=model.email,
        )

    async def create(self, booking: BookingEntity) -> BookingEntity:
        db_booking = Booking(
            user_id=booking.user_id,
            room_name=booking.room_name,
            reason=booking.reason,
            time=booking.time,
            status=booking.status.value,
            customer_name=booking.customer_name,
            customer_phone=booking.customer_phone,
            note=booking.note,
            email=booking.email,
        )
        self.db.add(db_booking)
        await self.db.commit()
        await self.db.refresh(db_booking)
        return self._to_entity(db_booking)

    async def get_by_id(self, booking_id: int) -> Optional[BookingEntity]:
        result = await self.db.execute(
            select(Booking).where(Booking.booking_id == booking_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_recent_by_user_id(self, user_id: int, limit: int = 10) -> List[BookingEntity]:
        result = await self.db.execute(
            select(Booking)
            .where(Booking.user_id == user_id)
            .order_by(Booking.time.desc())
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def update(self, booking: BookingEntity) -> BookingEntity:
        result = await self.db.execute(
            select(Booking).where(Booking.booking_id == booking.booking_id)
        )
        db_booking = result.scalar_one()
        db_booking.room_name = booking.room_name
        db_booking.reason = booking.reason
        db_booking.time = booking.time
        db_booking.status = booking.status.value
        db_booking.customer_name = booking.customer_name
        db_booking.customer_phone = booking.customer_phone
        db_booking.note = booking.note
        db_booking.email = booking.email
        await self.db.commit()
        await self.db.refresh(db_booking)
        return self._to_entity(db_booking)
