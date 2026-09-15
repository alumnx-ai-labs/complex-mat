from collections.abc import Generator
from datetime import date, time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.db.session import Base, get_db
from app.main import app
from app.models.meeting import Meeting, MeetingAttendee
from app.models.task import Task, TaskStatus
from app.models.user import Role, User

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=_engine)
    session = _TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=_engine)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session
        db_session.commit()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db_session: Session):
    counter = {"n": 0}

    def _make_user(
        role: Role = Role.TEAM_MEMBER,
        is_active: bool = True,
        password: str = "Password123!",
        employee_name: str | None = None,
    ) -> tuple[User, str]:
        counter["n"] += 1
        user = User(
            employee_name=employee_name or f"Test User {counter['n']}",
            employee_mail_id=f"user{counter['n']}@example.com",
            employee_id=f"E{1000 + counter['n']}",
            password_hash=hash_password(password),
            role=role,
            is_active=is_active,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user, password

    return _make_user


@pytest.fixture()
def auth_header():
    def _auth_header(user: User) -> dict[str, str]:
        token = create_access_token(subject=user.id)
        return {"Authorization": f"Bearer {token}"}

    return _auth_header


@pytest.fixture()
def make_meeting(db_session: Session):
    counter = {"n": 0}

    def _make_meeting(owner: User, attendees: list[User]) -> Meeting:
        counter["n"] += 1
        meeting = Meeting(
            title=f"Test Meeting {counter['n']}",
            date=date(2026, 9, 20),
            time=time(10, 0),
            agenda_notes=None,
            owner_id=owner.id,
        )
        db_session.add(meeting)
        db_session.flush()
        attendee_ids = {owner.id, *(attendee.id for attendee in attendees)}
        meeting.attendees = [
            MeetingAttendee(meeting_id=meeting.id, user_id=user_id) for user_id in attendee_ids
        ]
        db_session.commit()
        db_session.refresh(meeting)
        return meeting

    return _make_meeting


@pytest.fixture()
def make_task(db_session: Session):
    counter = {"n": 0}

    def _make_task(
        meeting: Meeting,
        assignee: User,
        status: TaskStatus = TaskStatus.TODO,
        title: str | None = None,
        description_notes: str | None = None,
    ) -> Task:
        counter["n"] += 1
        task = Task(
            meeting_id=meeting.id,
            title=title or f"Test Task {counter['n']}",
            description_notes=description_notes,
            assignee_id=assignee.id,
            due_date=date(2026, 9, 25),
            status=status,
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        return task

    return _make_task
