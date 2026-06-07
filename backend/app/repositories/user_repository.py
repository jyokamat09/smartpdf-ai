"""User repository for database operations."""

import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.user import User

logger = logging.getLogger(__name__)


class UserRepository:
    """Handles all user database operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_supabase_id(self, supabase_id: str) -> User | None:
        """Get user by supabase ID."""
        result = await self.db.execute(select(User).where(User.supabase_id == supabase_id))
        return result.scalar_one_or_none()

    async def create(self, email: str, full_name: str | None, supabase_id: str) -> User:
        """Create a new user."""
        user = User(
            email=email,
            full_name=full_name,
            supabase_id=supabase_id,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        logger.info(f"Created user: {user.id}")
        return user

    async def get_or_create(self, email: str, full_name: str | None, supabase_id: str) -> User:
        """Get existing user or create new one."""
        user = await self.get_by_supabase_id(supabase_id)
        if not user:
            user = await self.create(email, full_name, supabase_id)
        return user
