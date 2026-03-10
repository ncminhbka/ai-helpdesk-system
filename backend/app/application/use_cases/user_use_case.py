"""User CRUD use case."""
from typing import Optional

from app.application.dtos.user_dto import UserCreate, UserResponse
from app.domain.entities.user_entity import UserEntity
from app.domain.exceptions import EmailAlreadyExistsError
from app.domain.interfaces.user_repository import IUserRepository
from app.infrastructure.security.jwt_bcrypt import get_password_hash # vi phạm clean architecture


class UserUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        return await self.user_repo.get_by_email(email)

    async def get_by_id(self, user_id: int) -> Optional[UserEntity]:
        return await self.user_repo.get_by_id(user_id)

    async def create(self, user_in: UserCreate) -> UserEntity:
        existing = await self.user_repo.get_by_email(user_in.email)
        if existing:
            raise EmailAlreadyExistsError(f"Email '{user_in.email}' is already registered.")
        entity = UserEntity(
            id=None,
            email=user_in.email,
            password_hash=get_password_hash(user_in.password),
            name=user_in.name,
        )
        return await self.user_repo.create(entity)

    @staticmethod
    def to_response(entity: UserEntity) -> UserResponse:
        return UserResponse(id=entity.id, email=entity.email, name=entity.name)
