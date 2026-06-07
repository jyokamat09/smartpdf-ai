"""Embedding generation service using sentence-transformers."""

import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generates vector embeddings for text chunks."""

    def __init__(self) -> None:
        """Load the embedding model."""
        logger.info("Loading embedding model...")
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.dimension = 384
        logger.info("Embedding model loaded!")

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        embeddings = self.model.encode(texts, normalize_embeddings=True, batch_size=32)
        logger.info(f"Generated {len(embeddings)} embeddings")
        return [e.tolist() for e in embeddings]


_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Return a singleton EmbeddingService instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
