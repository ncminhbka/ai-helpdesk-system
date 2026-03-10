"""Authentication use case."""
from typing import Optional

from app.domain.entities.user_entity import UserEntity
from app.domain.interfaces.user_repository import IUserRepository # CHỉ phụ thuộc vào tầng Domain
from app.infrastructure.security.jwt_bcrypt import verify_password


class AuthUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def authenticate(self, email: str, password: str) -> Optional[UserEntity]:
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
