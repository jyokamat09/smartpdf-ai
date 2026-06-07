"""Quiz generation API endpoints."""

import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from groq import Groq
from backend.app.core.database import get_db
from backend.app.core.config import get_settings
from backend.app.services.search_service import SearchService
from backend.app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/quiz", tags=["quiz"])
settings = get_settings()


class QuizRequest(BaseModel):
    """Schema for quiz generation request."""
    workspace_id: uuid.UUID
    document_id: uuid.UUID
    num_questions: int = 5
    quiz_type: str = "mcq"


class QuizOption(BaseModel):
    """Schema for MCQ option."""
    label: str
    text: str
    is_correct: bool


class QuizQuestion(BaseModel):
    """Schema for a quiz question."""
    question: str
    options: list[QuizOption]
    explanation: str


class QuizResponse(BaseModel):
    """Schema for quiz response."""
    questions: list[QuizQuestion]
    document_id: str
    total_questions: int


@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(
    payload: QuizRequest,
    db: AsyncSession = Depends(get_db),
) -> QuizResponse:
    """Generate a quiz from document content."""
    try:
        embedder = get_embedding_service()
        search = SearchService(db=db, embedder=embedder)

        chunks = await search.search(
            query="key concepts definitions important facts",
            workspace_id=payload.workspace_id,
            document_id=payload.document_id,
            top_k=10,
        )

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No content found for this document.",
            )

        context = "\n\n".join([c["content"] for c in chunks[:8]])

        client = Groq(api_key=settings.groq_api_key)

        prompt = f"""Based on the following document content, generate {payload.num_questions} multiple choice questions.

Document content:
{context}

Generate exactly {payload.num_questions} MCQ questions in this JSON format:
{{
  "questions": [
    {{
      "question": "Question text here?",
      "options": [
        {{"label": "A", "text": "Option A text", "is_correct": false}},
        {{"label": "B", "text": "Option B text", "is_correct": true}},
        {{"label": "C", "text": "Option C text", "is_correct": false}},
        {{"label": "D", "text": "Option D text", "is_correct": false}}
      ],
      "explanation": "Brief explanation of why the answer is correct"
    }}
  ]
}}

Return ONLY valid JSON, no other text."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2048,
        )

        import json
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)

        questions = [QuizQuestion(**q) for q in data["questions"]]
        logger.info(f"Generated {len(questions)} quiz questions")

        return QuizResponse(
            questions=questions,
            document_id=str(payload.document_id),
            total_questions=len(questions),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quiz generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate quiz",
        )
