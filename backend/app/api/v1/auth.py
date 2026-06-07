"""Authentication API endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas.user import UserCreate, UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register or retrieve a user from Supabase auth data."""
    repo = UserRepository(db)
    try:
        user = await repo.get_or_create(
            email=payload.email,
            full_name=payload.full_name,
            supabase_id=payload.supabase_id,
        )
        logger.info(f"User registered/retrieved: {user.id}")
        return user
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.get("/me/{supabase_id}", response_model=UserResponse)
async def get_me(
    supabase_id: str,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Get current user by supabase ID."""
    repo = UserRepository(db)
    user = await repo.get_by_supabase_id(supabase_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
