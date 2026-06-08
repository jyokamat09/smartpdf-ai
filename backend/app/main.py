"""Main FastAPI application entry point."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import get_settings
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.documents import router as documents_router
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.feedback import router as feedback_router
from backend.app.api.v1.email import router as email_router
from backend.app.api.v1.quiz import router as quiz_router
from backend.app.api.v1.admin import router as admin_router
from backend.app.api.v1.workspaces import router as workspaces_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="smartpdf-ai",
    description="AI-powered Document Intelligence Platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(feedback_router, prefix="/api/v1")
app.include_router(email_router, prefix="/api/v1")
app.include_router(quiz_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(workspaces_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root health check endpoint."""
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@app.get("/health")
async def health():
    """Health check endpoint."""
    logger.info("Health check called")
    return {"status": "healthy"}