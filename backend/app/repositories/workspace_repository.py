"""Workspace repository for database operations."""

import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole

logger = logging.getLogger(__name__)


class WorkspaceRepository:
    """Handles all workspace database operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    async def create(self, name: str, owner_id: uuid.UUID, slug: str, description: str = "") -> Workspace:
        """Create a new workspace."""
        workspace = Workspace(
            name=name,
            owner_id=owner_id,
            slug=slug,
            description=description,
        )
        self.db.add(workspace)
        await self.db.flush()

        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=owner_id,
            role=WorkspaceRole.OWNER,
        )
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(workspace)
        logger.info(f"Created workspace: {workspace.id}")
        return workspace

    async def get_by_id(self, workspace_id: uuid.UUID) -> Workspace | None:
        """Get workspace by ID."""
        result = await self.db.execute(select(Workspace).where(Workspace.id == workspace_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Workspace | None:
        """Get workspace by slug."""
        result = await self.db.execute(select(Workspace).where(Workspace.slug == slug))
        return result.scalar_one_or_none()

    async def get_user_workspaces(self, user_id: uuid.UUID) -> list[Workspace]:
        """Get all workspaces for a user."""
        result = await self.db.execute(
            select(Workspace).join(WorkspaceMember).where(WorkspaceMember.user_id == user_id)
        )
        return list(result.scalars().all())

    async def add_member(self, workspace_id: uuid.UUID, user_id: uuid.UUID, role: WorkspaceRole) -> WorkspaceMember:
        """Add a member to a workspace."""
        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role,
        )
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        logger.info(f"Added member {user_id} to workspace {workspace_id} as {role}")
        return member

    async def get_member_role(self, workspace_id: uuid.UUID, user_id: uuid.UUID) -> WorkspaceRole | None:
        """Get member role in a workspace."""
        result = await self.db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()
        return member.role if member else None

    async def remove_member(self, workspace_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Remove a member from a workspace."""
        result = await self.db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()
        if member:
            await self.db.delete(member)
            await self.db.flush()
            logger.info(f"Removed member {user_id} from workspace {workspace_id}")
