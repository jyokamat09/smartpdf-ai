"""Feedback model for storing user feedback on AI responses."""

import uuid
from sqlalchemy import String, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base, TimestampMixin, UUIDMixin
import enum


class FeedbackType(str, enum.Enum):
    """Feedback type enum."""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"


class Feedback(Base, UUIDMixin, TimestampMixin):
    """Stores user feedback on AI responses."""

    __tablename__ = "feedback"

    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=True, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    feedback_type: Mapped[FeedbackType] = mapped_column(Enum(FeedbackType), nullable=False)
    chunk_ids: Mapped[str] = mapped_column(Text, nullable=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=True)
