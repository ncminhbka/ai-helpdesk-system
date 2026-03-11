"""JWT implementation of ITokenService."""
from datetime import timedelta

from app.domain.interfaces.token_service import ITokenService
from app.infrastructure.config.settings import settings
from app.infrastructure.security.jwt_bcrypt import create_access_token


class JwtTokenService(ITokenService):
    def create_token(self, user_id: int, email: str) -> str:
        return create_access_token(
            data={"sub": str(user_id), "email": email},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
