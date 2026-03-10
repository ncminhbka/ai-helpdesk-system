from typing import List, Optional

from app.application.dtos.booking_dto import BookingCreateDTO, BookingResponseDTO, BookingUpdateDTO
from app.application.utils.helpers import parse_datetime
from app.domain.entities.booking_entity import BookingEntity
from app.domain.entities.enums import BookingStatus
from app.domain.exceptions import BookingNotFoundError, InvalidBookingStatusError
from app.domain.interfaces.booking_repository import IBookingRepository


class BookingUseCase:
    def __init__(self, booking_repo: IBookingRepository):
        self.booking_repo = booking_repo

    @staticmethod
    def _to_dto(entity: BookingEntity) -> BookingResponseDTO:
        return BookingResponseDTO(
            booking_id=entity.booking_id,
            user_id=entity.user_id,
            room_name=entity.room_name,
            reason=entity.reason,
            time=entity.time,
            status=entity.status,
            customer_name=entity.customer_name,
            customer_phone=entity.customer_phone,
            note=entity.note,
            email=entity.email,
        )

    async def create_booking(self, data: BookingCreateDTO) -> BookingResponseDTO:
        entity = BookingEntity(
            booking_id=None,
            user_id=data.user_id,
            room_name=data.room_name,
            reason=data.reason,
            time=data.time,
            status=BookingStatus.SCHEDULED,
            customer_name=data.customer_name,
            customer_phone=data.customer_phone,
            note=data.note,
            email=data.email,
        )
        saved = await self.booking_repo.create(entity)
        return self._to_dto(saved)

    async def get_booking_by_id(self, booking_id: int) -> Optional[BookingResponseDTO]:
        entity = await self.booking_repo.get_by_id(booking_id)
        return self._to_dto(entity) if entity else None

    async def get_recent_bookings_by_user(self, user_id: int, limit: int = 10) -> List[BookingResponseDTO]:
        entities = await self.booking_repo.get_recent_by_user_id(user_id, limit)
        return [self._to_dto(e) for e in entities]

    async def update_booking(self, booking_id: int, data: BookingUpdateDTO) -> BookingResponseDTO:
        entity = await self.booking_repo.get_by_id(booking_id)
        if not entity:
            raise BookingNotFoundError(f"Booking #{booking_id} not found.")
        if entity.status in (BookingStatus.FINISHED, BookingStatus.CANCELED):
            raise InvalidBookingStatusError(
                f"Cannot update booking #{booking_id}: status is '{entity.status.value}'."
            )

        if data.room_name is not None:
            entity.room_name = data.room_name
        if data.reason is not None:
            entity.reason = data.reason
        if data.time is not None:
            entity.time = data.time
        if data.customer_name is not None:
            entity.customer_name = data.customer_name
        if data.customer_phone is not None:
            entity.customer_phone = data.customer_phone
        if data.note is not None:
            entity.note = data.note
        if data.email is not None:
            entity.email = data.email

        updated = await self.booking_repo.update(entity)
        return self._to_dto(updated)

    async def cancel_booking(self, booking_id: int) -> BookingResponseDTO:
        entity = await self.booking_repo.get_by_id(booking_id)
        if not entity:
            raise BookingNotFoundError(f"Booking #{booking_id} not found.")
        if entity.status == BookingStatus.FINISHED:
            raise InvalidBookingStatusError(
                f"Cannot cancel booking #{booking_id}: already Finished."
            )
        if entity.status == BookingStatus.CANCELED:
            raise InvalidBookingStatusError(
                f"Booking #{booking_id} is already Canceled."
            )
        entity.status = BookingStatus.CANCELED
        updated = await self.booking_repo.update(entity)
        return self._to_dto(updated)
