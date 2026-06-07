"""Email service for sending emails."""

import logging
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

conf = ConnectionConfig(
    MAIL_USERNAME=settings.smtp_user,
    MAIL_PASSWORD=settings.smtp_password,
    MAIL_FROM=settings.smtp_user,
    MAIL_PORT=settings.smtp_port,
    MAIL_SERVER=settings.smtp_host,
    MAIL_FROM_NAME="SmartPDF AI",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)


class EmailService:
    """Handles all email sending operations."""

    def __init__(self) -> None:
        """Initialize FastMail client."""
        self.mail = FastMail(conf)

    async def send_notes(self, to_email: str, notes: list[dict]) -> None:
        """Send notes to user email."""
        notes_html = ""
        for i, note in enumerate(notes):
            notes_html += f"""
            <div style="margin-bottom:24px; padding:16px; border:1px solid #e8ddd5; border-radius:12px; background:#faf8f5;">
                <p style="font-size:12px; color:#9e8e86; margin-bottom:8px;">
                    {note.get('docName', 'General')} · {note.get('savedAt', '')}
                </p>
                <p style="font-size:14px; line-height:1.7; color:#2c2420;">{note.get('content', '')}</p>
            </div>
            """

        html = f"""
        <div style="font-family: sans-serif; max-width:600px; margin:0 auto; padding:32px;">
            <div style="text-align:center; margin-bottom:32px;">
                <h1 style="font-size:24px; color:#2c2420;">✦ SmartPDF AI</h1>
                <p style="color:#9e8e86; font-size:14px;">Your saved notes</p>
            </div>
            {notes_html}
            <p style="text-align:center; font-size:12px; color:#9e8e86; margin-top:32px;">
                Sent by SmartPDF AI · Your intelligent document companion
            </p>
        </div>
        """

        message = MessageSchema(
            subject=f"Your SmartPDF AI Notes ({len(notes)} notes)",
            recipients=[to_email],
            body=html,
            subtype=MessageType.html,
        )

        await self.mail.send_message(message)
        logger.info(f"Notes email sent to {to_email}")

    async def send_welcome(self, to_email: str, name: str) -> None:
        """Send welcome email to new user."""
        html = f"""
        <div style="font-family: sans-serif; max-width:600px; margin:0 auto; padding:32px;">
            <div style="text-align:center; margin-bottom:32px;">
                <h1 style="font-size:24px; color:#2c2420;">✦ Welcome to SmartPDF AI</h1>
            </div>
            <p style="font-size:15px; color:#2c2420;">Hi {name},</p>
            <p style="font-size:14px; color:#6b5c54; line-height:1.7; margin-top:12px;">
                Welcome to SmartPDF AI! You can now upload PDFs and chat with them using AI.
            </p>
            <div style="margin-top:24px; padding:16px; background:#f5f0eb; border-radius:12px;">
                <p style="font-size:13px; color:#6b5c54; margin:0;">
                    ✦ Upload any PDF, DOCX or PPTX<br>
                    ✦ Ask questions and get AI answers<br>
                    ✦ Save notes and export them<br>
                    ✦ Your feedback makes AI smarter
                </p>
            </div>
        </div>
        """
        message = MessageSchema(
            subject="Welcome to SmartPDF AI ✦",
            recipients=[to_email],
            body=html,
            subtype=MessageType.html,
        )
        await self.mail.send_message(message)
        logger.info(f"Welcome email sent to {to_email}")


def get_email_service() -> EmailService:
    """Return an EmailService instance."""
    return EmailService()
