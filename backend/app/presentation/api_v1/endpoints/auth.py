"""Auth endpoints: login and register."""
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.engine import get_db
from app.infrastructure.config.settings import settings
from app.infrastructure.security.jwt_bcrypt import create_access_token
from app.application.use_cases.auth_use_case import AuthUseCase
from app.application.use_cases.user_use_case import UserUseCase
from app.application.dtos.token_dto import Token
from app.application.dtos.user_dto import UserCreate, UserResponse

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db), # đây chính là chỗ gọi get_db() để lấy session
) -> Any:
    """OAuth2 compatible login endpoint."""
    user = await AuthUseCase.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=Token)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Register a new user and return access token."""
    existing = await UserUseCase.get_by_email(db, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists.",
        )

    user = await UserUseCase.create(db, user_in=user_in)

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}
