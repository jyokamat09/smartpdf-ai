"""User schemas for request and response validation."""

import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr
from backend.app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: str | None = None
    avatar_url: str | None = None


class UserCreate(UserBase):
    """Schema for creating a user."""
    supabase_id: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True
