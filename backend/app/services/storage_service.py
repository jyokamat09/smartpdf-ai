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
    """Handles all file storage operations with MinIO."""

    def __init__(self) -> None:
        """Initialize MinIO client."""
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False,
        )
        self.bucket = settings.minio_bucket
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(f"Created bucket: {self.bucket}")
        except S3Error as e:
            logger.error(f"Bucket error: {e}")
            raise

    def upload_file(self, file_data: bytes, filename: str, content_type: str) -> str:
        """Upload file to MinIO and return file path."""
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
            logger.info(f"Uploaded file: {file_path}")
            return file_path
        except S3Error as e:
            logger.error(f"Upload error: {e}")
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
            logger.error(f"URL generation error: {e}")
            raise

    def delete_file(self, file_path: str) -> None:
        """Delete a file from MinIO."""
        try:
            self.client.remove_object(self.bucket, file_path)
            logger.info(f"Deleted file: {file_path}")
        except S3Error as e:
            logger.error(f"Delete error: {e}")
            raise


def get_storage_service() -> StorageService:
    """Return a StorageService instance."""
    return StorageService()
