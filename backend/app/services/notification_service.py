import logging

from app.integrations.email_sender import EmailSender
from app.models.meeting import Meeting
from app.models.task import Task
from app.models.user import User

logger = logging.getLogger(__name__)


def notify_task_assigned(
    email_sender: EmailSender, task: Task, meeting: Meeting, assignee: User
) -> None:
    due = task.due_date.isoformat() if task.due_date else "No due date"
    subject = f"You've been assigned a task: {task.title}"
    body = (
        f"Hi {assignee.employee_name},\n\n"
        f"You have been assigned a new task in meeting \"{meeting.title}\".\n\n"
        f"Task: {task.title}\n"
        f"Due date: {due}\n"
        f"Description/Notes: {task.description_notes or '(none)'}\n"
    )
    try:
        email_sender.send(assignee.employee_mail_id, subject, body)
    except Exception:
        logger.exception("Failed to send task-assignment email for task %s", task.id)
