"""Feedback API endpoints."""

import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from backend.app.core.database import get_db
from backend.app.services.feedback_service import FeedbackService
from backend.app.models.feedback import FeedbackType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    """Schema for feedback request."""
    workspace_id: uuid.UUID
    document_id: uuid.UUID | None = None
    question: str
    answer: str
    feedback_type: FeedbackType
    chunk_ids: list[str] = []
    user_id: str | None = None


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""
    id: uuid.UUID
    feedback_type: FeedbackType
    message: str


@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
) -> FeedbackResponse:
    """Submit feedback for an AI response."""
    try:
        service = FeedbackService(db)
        feedback = await service.save_feedback(
            workspace_id=payload.workspace_id,
            question=payload.question,
            answer=payload.answer,
            feedback_type=payload.feedback_type,
            chunk_ids=payload.chunk_ids,
            document_id=payload.document_id,
            user_id=payload.user_id,
        )
        return FeedbackResponse(
            id=feedback.id,
            feedback_type=feedback.feedback_type,
            message="Feedback saved! This will improve future answers.",
        )
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save feedback",
        )
