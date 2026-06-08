"""Kafka service - stubbed out, no-op for now."""

import logging

logger = logging.getLogger(__name__)


class KafkaService:
    """No-op Kafka service. Workers not yet implemented."""

    async def publish_document_uploaded(self, doc_id: str, workspace_id: str) -> None:
        logger.info("[KAFKA STUB] document_uploaded: %s", doc_id)

    async def publish_document_ready(self, doc_id: str, workspace_id: str) -> None:
        logger.info("[KAFKA STUB] document_ready: %s", doc_id)

    async def publish_feedback_received(self, feedback_id: str, feedback_type: str) -> None:
        logger.info("[KAFKA STUB] feedback_received: %s", feedback_id)

    async def publish_email(self, to_email: str, subject: str, content: str) -> None:
        logger.info("[KAFKA STUB] email.send to: %s", to_email)


_kafka_service = None


def get_kafka_service() -> KafkaService:
    """Return singleton KafkaService instance."""
    global _kafka_service
    if _kafka_service is None:
        _kafka_service = KafkaService()
    return _kafka_service