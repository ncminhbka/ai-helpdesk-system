from typing import List, Optional

from app.application.dtos.ticket_dto import TicketCreateDTO, TicketResponseDTO, TicketUpdateDTO
from app.domain.entities.enums import TicketStatus
from app.domain.entities.ticket_entity import TicketEntity
from app.domain.exceptions import InvalidTicketStatusError, TicketNotFoundError
from app.domain.interfaces.ticket_repository import ITicketRepository


class TicketUseCase:
    def __init__(self, ticket_repo: ITicketRepository):
        self.ticket_repo = ticket_repo

    @staticmethod
    def _to_dto(entity: TicketEntity) -> TicketResponseDTO:
        return TicketResponseDTO(
            ticket_id=entity.ticket_id,
            user_id=entity.user_id,
            content=entity.content,
            description=entity.description,
            status=entity.status,
            customer_name=entity.customer_name,
            customer_phone=entity.customer_phone,
            email=entity.email,
            time=entity.time,
        )

    async def create_ticket(self, data: TicketCreateDTO) -> TicketResponseDTO:
        entity = TicketEntity(
            ticket_id=None,
            user_id=data.user_id,
            content=data.content,
            description=data.description,
            status=TicketStatus.PENDING,
            customer_name=data.customer_name,
            customer_phone=data.customer_phone,
            email=data.email,
        ) # có thể viết hàm helper để convert DTO sang Entity nếu thấy cần thiết, nhưng ở đây chỉ có 1 use case nên viết trực tiếp cũng ổn.
        saved = await self.ticket_repo.create(entity)
        return self._to_dto(saved)

    async def get_ticket_by_id(self, ticket_id: int) -> Optional[TicketResponseDTO]:
        entity = await self.ticket_repo.get_by_id(ticket_id)
        return self._to_dto(entity) if entity else None

    async def get_recent_tickets_by_user(self, user_id: int, limit: int = 10) -> List[TicketResponseDTO]:
        entities = await self.ticket_repo.get_recent_by_user_id(user_id, limit)
        return [self._to_dto(e) for e in entities]

    async def update_ticket(self, ticket_id: int, data: TicketUpdateDTO) -> TicketResponseDTO:
        entity = await self.ticket_repo.get_by_id(ticket_id)
        if not entity:
            raise TicketNotFoundError(f"Ticket #{ticket_id} not found.")
        if entity.status in (TicketStatus.FINISHED, TicketStatus.CANCELED):
            raise InvalidTicketStatusError(
                f"Cannot update ticket #{ticket_id}: status is '{entity.status.value}'."
            )

        if data.content is not None:
            entity.content = data.content
        if data.description is not None:
            entity.description = data.description
        if data.status is not None:
            valid_statuses = [s.value for s in TicketStatus]
            if data.status not in valid_statuses:
                raise InvalidTicketStatusError(
                    f"Invalid status '{data.status}'. Valid: {', '.join(valid_statuses)}"
                )
            entity.status = TicketStatus(data.status)
        if data.customer_name is not None:
            entity.customer_name = data.customer_name
        if data.customer_phone is not None:
            entity.customer_phone = data.customer_phone
        if data.email is not None:
            entity.email = data.email

        updated = await self.ticket_repo.update(entity)
        return self._to_dto(updated)
