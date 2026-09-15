import logging
import smtplib
from abc import ABC, abstractmethod
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailSender(ABC):
    @abstractmethod
    def send(self, to_email: str, subject: str, body: str) -> None: ...


class SmtpEmailSender(EmailSender):
    def send(self, to_email: str, subject: str, body: str) -> None:
        settings = get_settings()
        if not settings.smtp_host:
            logger.info("SMTP not configured; skipping email to %s: %s", to_email, subject)
            return

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.smtp_from_email
        message["To"] = to_email
        message.set_content(body)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            if settings.smtp_username:
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)


def get_email_sender() -> EmailSender:
    return SmtpEmailSender()
