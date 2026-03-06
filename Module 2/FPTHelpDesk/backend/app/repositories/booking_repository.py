import uuid
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus

class BookingRepository:
    
    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        room_name: Optional[str],
        customer_name: Optional[str],
        customer_phone: Optional[str],
        email: Optional[str],
        reason: str,
        time: datetime,
        note: Optional[str]
    ) -> Booking:
        booking = Booking(
            user_id=user_id,
            room_name=room_name,
            customer_name=customer_name,
            customer_phone=customer_phone,
            email=email,
            reason=reason,
            time=time,
            note=note,
            status=BookingStatus.SCHEDULED.value,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)
        return booking

    @staticmethod
    async def get_by_id(db: AsyncSession, booking_id: int) -> Optional[Booking]:
        result = await db.execute(
            select(Booking).where(Booking.booking_id == booking_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_recent_by_user_id(db: AsyncSession, user_id: int, limit: int = 10) -> List[Booking]:
        result = await db.execute(
            select(Booking)
            .where(Booking.user_id == user_id)
            .order_by(Booking.time.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update(db: AsyncSession, booking: Booking) -> Booking:
        await db.commit()
        await db.refresh(booking)
        return booking

