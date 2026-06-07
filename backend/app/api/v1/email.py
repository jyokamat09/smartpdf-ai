"""Email API endpoints."""

import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from backend.app.services.email_service import get_email_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/email", tags=["email"])


class SendNotesRequest(BaseModel):
    """Schema for sending notes via email."""
    to_email: EmailStr
    notes: list[dict]


class SendNotesResponse(BaseModel):
    """Schema for send notes response."""
    message: str
    sent_to: str


@router.post("/send-notes", response_model=SendNotesResponse)
async def send_notes(payload: SendNotesRequest) -> SendNotesResponse:
    """Send notes to user email."""
    try:
        email_service = get_email_service()
        await email_service.send_notes(
            to_email=payload.to_email,
            notes=payload.notes,
        )
        return SendNotesResponse(
            message="Notes sent successfully!",
            sent_to=payload.to_email,
        )
    except Exception as e:
        logger.error(f"Email error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}",
        )
