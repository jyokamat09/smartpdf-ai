"""Document repository for database operations."""

import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.document import Document, DocumentStatus, DocumentType

logger = logging.getLogger(__name__)


class DocumentRepository:
    """Handles all document database operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    async def create(
        self,
        name: str,
        original_filename: str,
        file_path: str,
        file_size: int,
        file_type: DocumentType,
        workspace_id: uuid.UUID,
        uploaded_by: uuid.UUID,
    ) -> Document:
        """Create a new document record."""
        document = Document(
            name=name,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            workspace_id=workspace_id,
            uploaded_by=uploaded_by,
            status=DocumentStatus.UPLOADED,
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)
        logger.info(f"Created document: {document.id}")
        return document

    async def get_by_id(self, document_id: uuid.UUID) -> Document | None:
        """Get document by ID."""
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_by_workspace(self, workspace_id: uuid.UUID) -> list[Document]:
        """Get all documents in a workspace."""
        result = await self.db.execute(
            select(Document).where(Document.workspace_id == workspace_id)
        )
        return list(result.scalars().all())

    async def update_status(self, document_id: uuid.UUID, status: DocumentStatus) -> Document | None:
        """Update document processing status."""
        document = await self.get_by_id(document_id)
        if document:
            document.status = status
            await self.db.flush()
            await self.db.refresh(document)
            logger.info(f"Updated document {document_id} status to {status}")
        return document
