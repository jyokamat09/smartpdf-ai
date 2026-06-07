"""AI chat service using Groq LLM."""

import logging
from groq import Groq
from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ChatService:
    """Handles AI chat using Groq LLM."""

    def __init__(self) -> None:
        """Initialize Groq client."""
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = "llama-3.3-70b-versatile"

    def _calculate_confidence(self, chunks: list[dict]) -> float:
        """Calculate confidence score based on chunk similarities."""
        if not chunks:
            return 0.0
        top_similarities = [c["similarity"] for c in chunks[:3]]
        avg = sum(top_similarities) / len(top_similarities)
        return round(min(avg * 100, 99.0), 1)

    def answer(self, question: str, context_chunks: list[dict]) -> dict:
        """Generate an answer using retrieved context chunks."""
        context = "\n\n".join([
            f"[Chunk {i+1}] {chunk['content']}"
            for i, chunk in enumerate(context_chunks)
        ])

        system_prompt = """You are a helpful AI assistant that answers questions based on document content.
Always base your answers on the provided context chunks.
If the answer is not in the context, say so clearly.
Be concise and accurate.
At the end of your answer, list which chunks you used as [Source: Chunk X]."""

        user_prompt = f"""Context from document:
{context}

Question: {question}

Answer based on the context above:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1024,
            )

            answer_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            confidence = self._calculate_confidence(context_chunks)

            citations = []
            for i, chunk in enumerate(context_chunks):
                citations.append({
                    "chunk_id": chunk["id"],
                    "chunk_index": chunk["chunk_index"],
                    "page_number": chunk["page_number"],
                    "document_id": chunk["document_id"],
                    "similarity": chunk["similarity"],
                    "excerpt": chunk["content"][:200] + "...",
                })

            logger.info(f"Generated answer using {tokens_used} tokens, confidence: {confidence}%")
            return {
                "answer": answer_text,
                "citations": citations,
                "tokens_used": tokens_used,
                "model": self.model,
                "confidence": confidence,
            }

        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise


def get_chat_service() -> ChatService:
    """Return a ChatService instance."""
    return ChatService()
