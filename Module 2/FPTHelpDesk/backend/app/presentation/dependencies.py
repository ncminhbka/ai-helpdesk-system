"""
FastAPI dependencies for authentication.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.engine import get_db
from app.infrastructure.security.jwt_bcrypt import decode_token
from app.application.use_cases.user_use_case import UserUseCase
from app.infrastructure.database.models.user_model import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise credentials_exception

    user = await UserUseCase.get_by_id(db, user_id_int)
    if user is None:
        raise credentials_exception

    return user
