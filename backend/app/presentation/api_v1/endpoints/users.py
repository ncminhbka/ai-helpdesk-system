"""User profile endpoint."""
from fastapi import APIRouter, Depends

from app.application.dtos.user_dto import UserResponse
from app.domain.entities.user_entity import UserEntity
from app.presentation.dependencies import get_current_user

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserEntity = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return UserResponse(id=current_user.id, email=current_user.email, name=current_user.name)
