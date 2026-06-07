"""Chat API endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.services.search_service import SearchService
from backend.app.services.embedding_service import get_embedding_service
from backend.app.services.chat_service import get_chat_service
from backend.app.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask", response_model=ChatResponse)
async def ask(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Ask a question about documents in a workspace."""
    try:
        embedder = get_embedding_service()
        search = SearchService(db=db, embedder=embedder)

        chunks = await search.search(
            query=payload.question,
            workspace_id=payload.workspace_id,
            document_id=payload.document_id,
            top_k=payload.top_k,
        )

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No relevant content found for your question.",
            )

        chat = get_chat_service()
        result = chat.answer(
            question=payload.question,
            context_chunks=chunks,
        )

        logger.info(f"Chat answer generated for workspace: {payload.workspace_id}")
        return ChatResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate answer",
        )
