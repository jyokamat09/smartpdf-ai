"""Semantic search service using pgvector."""

import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class SearchService:
    """Performs semantic search over document chunks."""

    def __init__(self, db: AsyncSession, embedder: EmbeddingService) -> None:
        """Initialize with database session and embedder."""
        self.db = db
        self.embedder = embedder

    async def search(
        self,
        query: str,
        workspace_id: uuid.UUID,
        document_id: uuid.UUID | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        """Search for relevant chunks using vector similarity."""
        query_embedding = self.embedder.embed_text(query)
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        if document_id:
            sql = text("""
                SELECT
                    id,
                    content,
                    chunk_index,
                    page_number,
                    document_id,
                    relevance_score,
                    1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
                FROM document_chunks
                WHERE workspace_id = CAST(:workspace_id AS uuid)
                AND document_id = CAST(:document_id AS uuid)
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
            """)
            result = await self.db.execute(sql, {
                "embedding": embedding_str,
                "workspace_id": str(workspace_id),
                "document_id": str(document_id),
                "top_k": top_k,
            })
        else:
            sql = text("""
                SELECT
                    id,
                    content,
                    chunk_index,
                    page_number,
                    document_id,
                    relevance_score,
                    1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
                FROM document_chunks
                WHERE workspace_id = CAST(:workspace_id AS uuid)
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
            """)
            result = await self.db.execute(sql, {
                "embedding": embedding_str,
                "workspace_id": str(workspace_id),
                "top_k": top_k,
            })

        rows = result.fetchall()
        chunks = []
        for row in rows:
            chunks.append({
                "id": str(row.id),
                "content": row.content,
                "chunk_index": row.chunk_index,
                "page_number": row.page_number,
                "document_id": str(row.document_id),
                "similarity": float(row.similarity),
            })

        logger.info(f"Found {len(chunks)} relevant chunks for query")
        return chunks
