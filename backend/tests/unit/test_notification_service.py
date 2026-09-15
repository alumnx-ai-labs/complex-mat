from datetime import date, time

from app.integrations.email_sender import EmailSender
from app.models.meeting import Meeting
from app.models.task import Task, TaskStatus
from app.models.user import Role, User
from app.services import notification_service


class _RecordingEmailSender(EmailSender):
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    def send(self, to_email: str, subject: str, body: str) -> None:
        self.sent.append((to_email, subject, body))


class _FailingEmailSender(EmailSender):
    def send(self, to_email: str, subject: str, body: str) -> None:
        raise RuntimeError("SMTP is down")


def _make_task() -> tuple[Task, Meeting, User]:
    meeting = Meeting(
        id=1, title="Q3 Roadmap Review", date=date(2026, 9, 15), time=time(14, 0), owner_id=1
    )
    task = Task(
        id=1,
        meeting_id=1,
        title="Prepare onboarding design doc",
        description_notes="See related notes.",
        assignee_id=2,
        due_date=date(2026, 9, 20),
        status=TaskStatus.TODO,
    )
    assignee = User(
        id=2,
        employee_name="Sarah Chen",
        employee_mail_id="sarah@example.com",
        employee_id="E1002",
        password_hash="hash",
        role=Role.TEAM_MEMBER,
    )
    return task, meeting, assignee


def test_notify_task_assigned_sends_email_with_expected_context() -> None:
    task, meeting, assignee = _make_task()
    sender = _RecordingEmailSender()

    notification_service.notify_task_assigned(sender, task, meeting, assignee)

    assert len(sender.sent) == 1
    to_email, subject, body = sender.sent[0]
    assert to_email == "sarah@example.com"
    assert task.title in subject
    assert meeting.title in body
    assert "2026-09-20" in body
    assert task.description_notes in body


def test_notify_task_assigned_swallows_email_delivery_failure() -> None:
    task, meeting, assignee = _make_task()
    sender = _FailingEmailSender()

    notification_service.notify_task_assigned(sender, task, meeting, assignee)


def test_notify_task_assigned_handles_missing_due_date_and_description() -> None:
    task, meeting, assignee = _make_task()
    task.due_date = None
    task.description_notes = None
    sender = _RecordingEmailSender()

    notification_service.notify_task_assigned(sender, task, meeting, assignee)

    assert len(sender.sent) == 1
    _, _, body = sender.sent[0]
    assert "No due date" in body
    assert "(none)" in body
