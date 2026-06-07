"""Document schemas for request and response validation."""

import uuid
from datetime import datetime
from pydantic import BaseModel
from backend.app.models.document import DocumentStatus, DocumentType


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: uuid.UUID
    name: str
    original_filename: str
    file_path: str
    file_size: int
    file_type: DocumentType
    status: DocumentStatus
    page_count: int | None
    chunk_count: int | None
    workspace_id: uuid.UUID
    uploaded_by: uuid.UUID
    summary: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for list of documents."""
    documents: list[DocumentResponse]
    total: int
