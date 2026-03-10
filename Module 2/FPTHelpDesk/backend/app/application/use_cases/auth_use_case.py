"""Authentication use case."""
from typing import Optional

from app.domain.entities.user_entity import UserEntity
from app.domain.interfaces.security import IPasswordHasher
from app.domain.interfaces.user_repository import IUserRepository


class AuthUseCase:
    def __init__(self, user_repo: IUserRepository, hasher: IPasswordHasher):
        self.user_repo = user_repo
        self.hasher = hasher

    async def authenticate(self, email: str, password: str) -> Optional[UserEntity]:
        user = await self.user_repo.get_by_email(email)
        if not user or not self.hasher.verify(password, user.password_hash):
            return None
        return user
