"""Kafka/Redpanda messaging service."""

import json
import logging
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

TOPICS = {
    "document_uploaded": "document.uploaded",
    "document_processing": "document.processing",
    "document_ready": "document.ready",
    "feedback_received": "feedback.received",
    "email_send": "email.send",
    "notification_send": "notification.send",
}


class KafkaService:
    """Handles Kafka message publishing."""

    def __init__(self) -> None:
        """Initialize Kafka producer."""
        self.bootstrap_servers = "localhost:19092"
        self._producer = None

    async def start(self) -> None:
        """Start the Kafka producer."""
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await self._producer.start()
        logger.info("Kafka producer started")

    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if self._producer:
            await self._producer.stop()
            logger.info("Kafka producer stopped")

    async def publish(self, topic: str, message: dict) -> None:
        """Publish a message to a Kafka topic."""
        if not self._producer:
            await self.start()
        try:
            await self._producer.send_and_wait(topic, message)
            logger.info(f"Published to {topic}: {message}")
        except Exception as e:
            logger.error(f"Kafka publish error: {e}")
            raise

    async def publish_document_uploaded(self, document_id: str, workspace_id: str) -> None:
        """Publish document uploaded event."""
        await self.publish(TOPICS["document_uploaded"], {
            "event": "document.uploaded",
            "document_id": document_id,
            "workspace_id": workspace_id,
        })

    async def publish_document_ready(self, document_id: str, workspace_id: str) -> None:
        """Publish document ready event."""
        await self.publish(TOPICS["document_ready"], {
            "event": "document.ready",
            "document_id": document_id,
            "workspace_id": workspace_id,
        })

    async def publish_feedback_received(self, feedback_id: str, feedback_type: str) -> None:
        """Publish feedback received event."""
        await self.publish(TOPICS["feedback_received"], {
            "event": "feedback.received",
            "feedback_id": feedback_id,
            "feedback_type": feedback_type,
        })

    async def publish_email(self, to_email: str, subject: str, content: str) -> None:
        """Publish email send event."""
        await self.publish(TOPICS["email_send"], {
            "event": "email.send",
            "to_email": to_email,
            "subject": subject,
            "content": content,
        })


_kafka_service = None


def get_kafka_service() -> KafkaService:
    """Return singleton KafkaService instance."""
    global _kafka_service
    if _kafka_service is None:
        _kafka_service = KafkaService()
    return _kafka_service
