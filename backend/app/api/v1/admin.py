"""Admin dashboard API endpoints."""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from backend.app.core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


class AdminStats(BaseModel):
    """Schema for admin stats response."""
    total_users: int
    total_documents: int
    total_chunks: int
    total_feedback: int
    documents_by_status: dict
    storage_used_mb: float


@router.get("/stats", response_model=AdminStats)
async def get_stats(db: AsyncSession = Depends(get_db)) -> AdminStats:
    """Get admin dashboard statistics."""
    try:
        users = await db.execute(text("SELECT COUNT(*) FROM users"))
        total_users = users.scalar()

        docs = await db.execute(text("SELECT COUNT(*) FROM documents"))
        total_documents = docs.scalar()

        chunks = await db.execute(text("SELECT COUNT(*) FROM document_chunks"))
        total_chunks = chunks.scalar()

        feedback = await db.execute(text("SELECT COUNT(*) FROM feedback"))
        total_feedback = feedback.scalar()

        status_result = await db.execute(text("SELECT status, COUNT(*) FROM documents GROUP BY status"))
        documents_by_status = {row[0]: row[1] for row in status_result.fetchall()}

        size_result = await db.execute(text("SELECT COALESCE(SUM(file_size), 0) FROM documents"))
        total_bytes = size_result.scalar()
        storage_used_mb = round(total_bytes / (1024 * 1024), 2)

        return AdminStats(
            total_users=total_users,
            total_documents=total_documents,
            total_chunks=total_chunks,
            total_feedback=total_feedback,
            documents_by_status=documents_by_status,
            storage_used_mb=storage_used_mb,
        )
    except Exception as e:
        logger.error(f"Admin stats error: {e}")
        raise
