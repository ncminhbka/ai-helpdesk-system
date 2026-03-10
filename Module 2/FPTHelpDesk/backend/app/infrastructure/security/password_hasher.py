"""Bcrypt implementation of IPasswordHasher."""
from app.domain.interfaces.security import IPasswordHasher
from app.infrastructure.security.jwt_bcrypt import get_password_hash, verify_password


class BcryptPasswordHasher(IPasswordHasher):
    def hash(self, plain_password: str) -> str:
        return get_password_hash(plain_password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return verify_password(plain_password, hashed_password)
