"""Document API endpoints."""

import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.services.storage_service import get_storage_service, StorageService
from backend.app.services.extraction_service import get_extraction_service
from backend.app.services.chunking_service import get_chunking_service
from backend.app.services.embedding_service import get_embedding_service
from backend.app.services.document_processor import DocumentProcessor
from backend.app.services.kafka_service import get_kafka_service
from backend.app.schemas.document import DocumentResponse, DocumentListResponse
from backend.app.models.document import DocumentType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_TYPES = {
    "application/pdf": DocumentType.PDF,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocumentType.DOCX,
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": DocumentType.PPTX,
    "text/plain": DocumentType.TXT,
    "text/markdown": DocumentType.MD,
}

MAX_FILE_SIZE = 50 * 1024 * 1024


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    workspace_id: uuid.UUID,
    uploaded_by: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> DocumentResponse:
    """Upload a document and trigger background processing."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not supported.",
        )

    file_data = await file.read()

    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 50MB",
        )

    try:
        file_path = storage.upload_file(
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type,
        )

        repo = DocumentRepository(db)
        document = await repo.create(
            name=file.filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(file_data),
            file_type=ALLOWED_TYPES[file.content_type],
            workspace_id=workspace_id,
            uploaded_by=uploaded_by,
        )

        await db.commit()

        background_tasks.add_task(process_document_background, document.id, str(workspace_id))

        logger.info(f"Document uploaded: {document.id}")
        return document

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed",
        )


async def process_document_background(document_id: uuid.UUID, workspace_id: str) -> None:
    """Background task to process a document and publish Kafka events."""
    from backend.app.core.database import AsyncSessionLocal
    kafka = get_kafka_service()
    async with AsyncSessionLocal() as db:
        try:
            await kafka.publish_document_uploaded(str(document_id), workspace_id)

            processor = DocumentProcessor(
                db=db,
                extractor=get_extraction_service(),
                chunker=get_chunking_service(),
                embedder=get_embedding_service(),
                storage=get_storage_service(),
            )
            await processor.process(document_id)
            await db.commit()

            await kafka.publish_document_ready(str(document_id), workspace_id)
            logger.info(f"Background processing complete: {document_id}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Background processing failed: {e}")


@router.get("/workspace/{workspace_id}", response_model=DocumentListResponse)
async def list_documents(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """List all documents in a workspace."""
    repo = DocumentRepository(db)
    documents = await repo.get_by_workspace(workspace_id)
    return DocumentListResponse(documents=documents, total=len(documents))


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Get a document by ID."""
    repo = DocumentRepository(db)
    document = await repo.get_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return document
