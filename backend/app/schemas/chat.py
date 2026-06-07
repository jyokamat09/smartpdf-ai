"""Chat schemas for request and response validation."""

import uuid
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Schema for chat request."""
    question: str
    workspace_id: uuid.UUID
    document_id: uuid.UUID | None = None
    top_k: int = 5


class Citation(BaseModel):
    """Schema for a citation."""
    chunk_id: str
    chunk_index: int
    page_number: int | None
    document_id: str
    similarity: float
    excerpt: str


class ChatResponse(BaseModel):
    """Schema for chat response."""
    answer: str
    citations: list[Citation]
    tokens_used: int
    model: str
    confidence: float = 0.0
