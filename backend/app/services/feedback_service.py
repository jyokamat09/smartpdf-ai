"""Feedback service for storing and applying user feedback."""

import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from backend.app.models.feedback import Feedback, FeedbackType
from backend.app.models.chunk import DocumentChunk

logger = logging.getLogger(__name__)


class FeedbackService:
    """Handles feedback storage and learning."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    async def save_feedback(
        self,
        workspace_id: uuid.UUID,
        question: str,
        answer: str,
        feedback_type: FeedbackType,
        chunk_ids: list[str],
        document_id: uuid.UUID | None = None,
        user_id: str | None = None,
    ) -> Feedback:
        """Save feedback and immediately update chunk relevance scores."""
        feedback = Feedback(
            workspace_id=workspace_id,
            document_id=document_id,
            question=question,
            answer=answer,
            feedback_type=feedback_type,
            chunk_ids=",".join(chunk_ids),
            user_id=user_id,
        )
        self.db.add(feedback)
        await self.db.flush()

        await self._apply_feedback(chunk_ids, feedback_type)
        logger.info(f"Saved feedback: {feedback_type} for {len(chunk_ids)} chunks")
        return feedback

    async def _apply_feedback(
        self,
        chunk_ids: list[str],
        feedback_type: FeedbackType,
    ) -> None:
        """Update chunk relevance scores based on feedback."""
        if not chunk_ids:
            return

        delta = 0.1 if feedback_type == FeedbackType.THUMBS_UP else -0.1

        for chunk_id in chunk_ids:
            try:
                result = await self.db.execute(
                    select(DocumentChunk).where(DocumentChunk.id == uuid.UUID(chunk_id))
                )
                chunk = result.scalar_one_or_none()
                if chunk:
                    current = chunk.relevance_score or 1.0
                    chunk.relevance_score = max(0.1, min(2.0, current + delta))
            except Exception as e:
                logger.error(f"Error updating chunk {chunk_id}: {e}")

        await self.db.flush()
        logger.info(f"Applied {feedback_type} feedback to {len(chunk_ids)} chunks")
