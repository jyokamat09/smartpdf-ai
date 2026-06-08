"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """All app settings loaded from environment variables."""

    # App
    app_name: str = "smartpdf-ai"
    app_env: str = "development"
    app_port: int = 8000
    secret_key: str

    # Database
    database_url: str
    database_pool_size: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO / Backblaze B2
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str = "smartpdf-documents"

    # Groq
    groq_api_key: str

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str

    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    # Frontend
    next_public_api_url: str = "http://localhost:8000"
    next_public_supabase_url: str = ""
    next_public_supabase_anon_key: str = ""
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()