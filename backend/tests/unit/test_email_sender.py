from unittest.mock import MagicMock, patch

from app.core.config import Settings
from app.integrations.email_sender import EmailSender, SmtpEmailSender, get_email_sender


def _settings(**overrides) -> Settings:
    defaults = dict(
        smtp_host="",
        smtp_port=587,
        smtp_username="",
        smtp_password="",
        smtp_from_email="mat-notifications@example.com",
    )
    defaults.update(overrides)
    return Settings(**defaults)


def test_send_skips_smtp_entirely_when_host_not_configured():
    sender = SmtpEmailSender()

    with patch("app.integrations.email_sender.get_settings", return_value=_settings()):
        with patch("app.integrations.email_sender.smtplib.SMTP") as smtp_cls:
            sender.send("sarah@example.com", "Subject", "Body")

    smtp_cls.assert_not_called()


def test_send_uses_smtp_without_login_when_no_credentials_configured():
    sender = SmtpEmailSender()
    server = MagicMock()
    smtp_cls = MagicMock()
    smtp_cls.return_value.__enter__.return_value = server

    settings = _settings(smtp_host="smtp.example.com", smtp_port=2525)
    with patch("app.integrations.email_sender.get_settings", return_value=settings):
        with patch("app.integrations.email_sender.smtplib.SMTP", smtp_cls):
            sender.send("sarah@example.com", "You've been assigned a task", "Hi Sarah")

    smtp_cls.assert_called_once_with("smtp.example.com", 2525, timeout=10)
    server.starttls.assert_not_called()
    server.login.assert_not_called()
    assert server.send_message.call_count == 1
    sent_message = server.send_message.call_args[0][0]
    assert sent_message["To"] == "sarah@example.com"
    assert sent_message["Subject"] == "You've been assigned a task"
    assert sent_message["From"] == "mat-notifications@example.com"


def test_send_authenticates_when_credentials_are_configured():
    sender = SmtpEmailSender()
    server = MagicMock()
    smtp_cls = MagicMock()
    smtp_cls.return_value.__enter__.return_value = server

    settings = _settings(
        smtp_host="smtp.example.com", smtp_username="bot", smtp_password="secret"
    )
    with patch("app.integrations.email_sender.get_settings", return_value=settings):
        with patch("app.integrations.email_sender.smtplib.SMTP", smtp_cls):
            sender.send("sarah@example.com", "Subject", "Body")

    server.starttls.assert_called_once()
    server.login.assert_called_once_with("bot", "secret")
    server.send_message.assert_called_once()


def test_send_propagates_smtp_errors_to_the_caller():
    sender = SmtpEmailSender()
    smtp_cls = MagicMock()
    smtp_cls.return_value.__enter__.side_effect = OSError("connection refused")

    settings = _settings(smtp_host="smtp.example.com")
    with patch("app.integrations.email_sender.get_settings", return_value=settings):
        with patch("app.integrations.email_sender.smtplib.SMTP", smtp_cls):
            try:
                sender.send("sarah@example.com", "Subject", "Body")
                raised = False
            except OSError:
                raised = True

    assert raised, "SmtpEmailSender.send should propagate delivery errors to its caller"


def test_get_email_sender_returns_an_smtp_email_sender():
    sender = get_email_sender()

    assert isinstance(sender, SmtpEmailSender)
    assert isinstance(sender, EmailSender)
