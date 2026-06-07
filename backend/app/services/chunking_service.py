"""Text chunking service for splitting documents into chunks."""

import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class ChunkingService:
    """Splits text into overlapping chunks for embedding."""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ) -> None:
        """Initialize the text splitter."""
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", " ", ""],
        )

    def chunk_text(self, text: str) -> list[str]:
        """Split text into chunks.
        
        Returns:
            List of text chunks.
        """
        chunks = self.splitter.split_text(text)
        cleaned = [c.strip() for c in chunks if c.strip()]
        logger.info(f"Split text into {len(cleaned)} chunks")
        return cleaned


def get_chunking_service() -> ChunkingService:
    """Return a ChunkingService instance."""
    return ChunkingService()
