"""MinIO storage service for file operations."""

import logging
import uuid
from io import BytesIO
from minio import Minio
from minio.error import S3Error
from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class StorageService:
    """Handles all file storage operations with Backblaze B2."""

    def __init__(self) -> None:
        """Initialize MinIO client."""
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=True,
        )
        self.bucket = settings.minio_bucket
        # bucket already created manually on Backblaze

    def upload_file(self, file_data: bytes, filename: str, content_type: str) -> str:
        """Upload file to Backblaze B2 and return file path."""
        file_id = str(uuid.uuid4())
        extension = filename.rsplit(".", 1)[-1].lower()
        file_path = f"documents/{file_id}.{extension}"

        try:
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=file_path,
                data=BytesIO(file_data),
                length=len(file_data),
                content_type=content_type,
            )
            logger.info("Uploaded file: %s", file_path)
            return file_path
        except S3Error as e:
            logger.error("Upload error: %s", e)
            raise

    def get_file_url(self, file_path: str, expires_hours: int = 24) -> str:
        """Get a presigned URL for a file."""
        from datetime import timedelta
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket,
                object_name=file_path,
                expires=timedelta(hours=expires_hours),
            )
            return url
        except S3Error as e:
            logger.error("URL generation error: %s", e)
            raise

    def delete_file(self, file_path: str) -> None:
        """Delete a file from Backblaze B2."""
        try:
            self.client.remove_object(self.bucket, file_path)
            logger.info("Deleted file: %s", file_path)
        except S3Error as e:
            logger.error("Delete error: %s", e)
            raise


_storage_service = None


def get_storage_service() -> StorageService:
    """Return a singleton StorageService instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service