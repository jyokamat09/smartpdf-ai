"""Document processing service that orchestrates extraction, chunking, and embedding."""

import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.services.extraction_service import ExtractionService
from backend.app.services.chunking_service import ChunkingService
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.storage_service import StorageService
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.models.document import DocumentStatus
from backend.app.models.chunk import DocumentChunk

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Orchestrates the full document processing pipeline."""

    def __init__(
        self,
        db: AsyncSession,
        extractor: ExtractionService,
        chunker: ChunkingService,
        embedder: EmbeddingService,
        storage: StorageService,
    ) -> None:
        """Initialize with all required services."""
        self.db = db
        self.extractor = extractor
        self.chunker = chunker
        self.embedder = embedder
        self.storage = storage
        self.doc_repo = DocumentRepository(db)

    async def process(self, document_id: uuid.UUID) -> None:
        """Process a document through the full pipeline."""
        logger.info(f"Starting processing for document: {document_id}")

        document = await self.doc_repo.get_by_id(document_id)
        if not document:
            logger.error(f"Document not found: {document_id}")
            return

        await self.doc_repo.update_status(document_id, DocumentStatus.PROCESSING)

        try:
            # Step 1: Download file from MinIO
            response = self.storage.client.get_object(
                self.storage.bucket, document.file_path
            )
            file_data = response.read()
            response.close()

            # Step 2: Extract text
            text, page_count = self.extractor.extract(file_data, document.file_type.value)
            document.page_count = page_count
            await self.db.flush()

            # Step 3: Chunk text
            await self.doc_repo.update_status(document_id, DocumentStatus.CHUNKED)
            chunks = self.chunker.chunk_text(text)

            # Step 4: Generate embeddings
            await self.doc_repo.update_status(document_id, DocumentStatus.EMBEDDED)
            embeddings = self.embedder.embed_batch(chunks)

            # Step 5: Save chunks to database
            for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                chunk = DocumentChunk(
                    document_id=document_id,
                    workspace_id=document.workspace_id,
                    content=chunk_text,
                    chunk_index=i,
                    embedding=embedding,
                    relevance_score=1.0,
                )
                self.db.add(chunk)

            document.chunk_count = len(chunks)
            await self.db.flush()

            await self.doc_repo.update_status(document_id, DocumentStatus.READY)
            logger.info(f"Document {document_id} processed: {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"Processing failed for {document_id}: {e}")
            await self.doc_repo.update_status(document_id, DocumentStatus.FAILED)
            raise
