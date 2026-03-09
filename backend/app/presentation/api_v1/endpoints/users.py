"""User profile endpoint."""
from fastapi import APIRouter, Depends
from app.presentation.dependencies import get_current_user
from app.infrastructure.database.models.user_model import User
from app.application.dtos.user_dto import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return current_user
