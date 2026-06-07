"""Workspace API endpoints."""

import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from backend.app.core.database import get_db
from backend.app.repositories.workspace_repository import WorkspaceRepository
from backend.app.models.workspace import WorkspaceRole

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class WorkspaceCreate(BaseModel):
    """Schema for creating a workspace."""
    name: str
    description: str = ""
    owner_id: uuid.UUID


class WorkspaceResponse(BaseModel):
    """Schema for workspace response."""
    id: uuid.UUID
    name: str
    description: str | None
    owner_id: uuid.UUID
    slug: str

    class Config:
        from_attributes = True


class AddMemberRequest(BaseModel):
    """Schema for adding a member."""
    user_id: uuid.UUID
    role: WorkspaceRole = WorkspaceRole.MEMBER


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
) -> WorkspaceResponse:
    """Create a new workspace."""
    repo = WorkspaceRepository(db)
    slug = payload.name.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8]
    existing = await repo.get_by_slug(slug)
    if existing:
        raise HTTPException(status_code=400, detail="Workspace slug already exists")
    workspace = await repo.create(
        name=payload.name,
        owner_id=payload.owner_id,
        slug=slug,
        description=payload.description,
    )
    return workspace


@router.get("/user/{user_id}", response_model=list[WorkspaceResponse])
async def get_user_workspaces(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[WorkspaceResponse]:
    """Get all workspaces for a user."""
    repo = WorkspaceRepository(db)
    workspaces = await repo.get_user_workspaces(user_id)
    return workspaces


@router.post("/{workspace_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member(
    workspace_id: uuid.UUID,
    payload: AddMemberRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Add a member to a workspace."""
    repo = WorkspaceRepository(db)
    workspace = await repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    member = await repo.add_member(workspace_id, payload.user_id, payload.role)
    return {"message": "Member added", "role": member.role}


@router.delete("/{workspace_id}/members/{user_id}")
async def remove_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Remove a member from a workspace."""
    repo = WorkspaceRepository(db)
    await repo.remove_member(workspace_id, user_id)
    return {"message": "Member removed"}


@router.get("/{workspace_id}/role/{user_id}")
async def get_member_role(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a member role in a workspace."""
    repo = WorkspaceRepository(db)
    role = await repo.get_member_role(workspace_id, user_id)
    if not role:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"role": role}
