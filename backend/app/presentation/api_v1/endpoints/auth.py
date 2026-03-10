"""Auth endpoints: login and register."""
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.application.dtos.token_dto import Token
from app.application.dtos.user_dto import UserCreate
from app.application.use_cases.auth_use_case import AuthUseCase
from app.application.use_cases.user_use_case import UserUseCase
from app.domain.exceptions import EmailAlreadyExistsError
from app.infrastructure.config.settings import settings
from app.infrastructure.security.jwt_bcrypt import create_access_token
from app.presentation.dependencies import get_auth_use_case, get_user_use_case

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    use_case: AuthUseCase = Depends(get_auth_use_case),
) -> Any:
    """OAuth2 compatible login endpoint."""
    user = await use_case.authenticate(email=form_data.username, password=form_data.password)
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
    use_case: UserUseCase = Depends(get_user_use_case),
) -> Any:
    """Register a new user and return access token."""
    try:
        user = await use_case.create(user_in)
    except EmailAlreadyExistsError:
        raise HTTPException(status_code=400, detail="A user with this email already exists.")

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}
