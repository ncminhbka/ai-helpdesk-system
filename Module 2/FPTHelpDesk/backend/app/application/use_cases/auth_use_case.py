"""Authentication use case."""
from typing import Optional

from app.domain.entities.user_entity import UserEntity
from app.domain.interfaces.security import IPasswordHasher
from app.domain.interfaces.token_service import ITokenService
from app.domain.interfaces.user_repository import IUserRepository


class AuthUseCase:
    def __init__(self, user_repo: IUserRepository, hasher: IPasswordHasher, token_service: ITokenService):
        self.user_repo = user_repo
        self.hasher = hasher
        self.token_service = token_service

    async def authenticate(self, email: str, password: str) -> Optional[UserEntity]:
        user = await self.user_repo.get_by_email(email)
        if not user or not self.hasher.verify(password, user.password_hash):
            return None
        return user

    def generate_token(self, user: UserEntity) -> str:
        return self.token_service.create_token(user.id, user.email)
