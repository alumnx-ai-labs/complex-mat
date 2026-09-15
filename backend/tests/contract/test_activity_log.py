from fastapi.testclient import TestClient

from app.models.activity_log import ActivityLogEntry
from app.models.user import Role
from app.services.activity_log_service import log_activity


def test_admin_sees_activity_log_entries_newest_first(
    client: TestClient, make_user, auth_header, db_session
):
    admin, _ = make_user(role=Role.ADMIN)
    other, _ = make_user(role=Role.TEAM_MEMBER)

    log_activity(db_session, admin.id, "MEETING_CREATED", "Meeting", 1)
    log_activity(db_session, other.id, "TASK_CREATED", "Task", 2)
    db_session.commit()

    response = client.get("/api/activity-log", headers=auth_header(admin))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["action"] == "TASK_CREATED"
    assert body[0]["actorName"] == other.employee_name
    assert body[1]["action"] == "MEETING_CREATED"
    for entry in body:
        assert set(entry.keys()) == {
            "id",
            "actorId",
            "actorName",
            "action",
            "entityType",
            "entityId",
            "timestamp",
        }


def test_team_member_cannot_view_the_activity_log(
    client: TestClient, make_user, auth_header
):
    member, _ = make_user(role=Role.TEAM_MEMBER)

    response = client.get("/api/activity-log", headers=auth_header(member))

    assert response.status_code == 403


def test_entity_type_filter_narrows_the_results(
    client: TestClient, make_user, auth_header, db_session
):
    admin, _ = make_user(role=Role.ADMIN)
    log_activity(db_session, admin.id, "MEETING_CREATED", "Meeting", 1)
    log_activity(db_session, admin.id, "TASK_CREATED", "Task", 2)
    db_session.commit()

    response = client.get(
        "/api/activity-log", params={"entityType": "Task"}, headers=auth_header(admin)
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["entityType"] == "Task"


def test_since_filter_excludes_older_entries(
    client: TestClient, make_user, auth_header, db_session
):
    admin, _ = make_user(role=Role.ADMIN)
    log_activity(db_session, admin.id, "MEETING_CREATED", "Meeting", 1)
    db_session.commit()

    entry = db_session.query(ActivityLogEntry).one()
    future = entry.timestamp.replace(year=entry.timestamp.year + 1)

    response = client.get(
        "/api/activity-log",
        params={"since": future.isoformat()},
        headers=auth_header(admin),
    )

    assert response.status_code == 200
    assert response.json() == []
