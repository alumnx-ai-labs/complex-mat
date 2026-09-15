from fastapi.testclient import TestClient

from app.models.user import Role


def test_admin_can_add_a_member_who_can_then_sign_in(client: TestClient, make_user, auth_header):
    admin, _ = make_user(role=Role.ADMIN)

    response = client.post(
        "/api/users",
        json={
            "employeeName": "Priya Nair",
            "employeeMailId": "priya@example.com",
            "employeeId": "EMP-1077",
            "password": "TempPass123!",
            "role": "TEAM_MEMBER",
        },
        headers=auth_header(admin),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["employeeMailId"] == "priya@example.com"
    assert body["role"] == "TEAM_MEMBER"
    assert body["isActive"] is True

    login = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": "priya@example.com",
            "password": "TempPass123!",
            "termsAccepted": True,
        },
    )
    assert login.status_code == 200


def test_team_member_cannot_add_a_member(client: TestClient, make_user, auth_header):
    member, _ = make_user(role=Role.TEAM_MEMBER)

    response = client.post(
        "/api/users",
        json={
            "employeeName": "New Person",
            "employeeMailId": "new.person@example.com",
            "employeeId": "EMP-9001",
            "password": "TempPass123!",
            "role": "TEAM_MEMBER",
        },
        headers=auth_header(member),
    )

    assert response.status_code == 403


def test_duplicate_employee_mail_id_is_rejected(client: TestClient, make_user, auth_header):
    admin, _ = make_user(role=Role.ADMIN)
    existing, _ = make_user(role=Role.TEAM_MEMBER)

    response = client.post(
        "/api/users",
        json={
            "employeeName": "Another Person",
            "employeeMailId": existing.employee_mail_id,
            "employeeId": "EMP-9002",
            "password": "TempPass123!",
            "role": "TEAM_MEMBER",
        },
        headers=auth_header(admin),
    )

    assert response.status_code == 409


def test_duplicate_employee_id_is_rejected(client: TestClient, make_user, auth_header):
    admin, _ = make_user(role=Role.ADMIN)
    existing, _ = make_user(role=Role.TEAM_MEMBER)

    response = client.post(
        "/api/users",
        json={
            "employeeName": "Another Person",
            "employeeMailId": "another.person@example.com",
            "employeeId": existing.employee_id,
            "password": "TempPass123!",
            "role": "TEAM_MEMBER",
        },
        headers=auth_header(admin),
    )

    assert response.status_code == 409


def test_missing_required_field_is_rejected(client: TestClient, make_user, auth_header):
    admin, _ = make_user(role=Role.ADMIN)

    response = client.post(
        "/api/users",
        json={
            "employeeName": "Incomplete Person",
            "employeeMailId": "incomplete@example.com",
            "employeeId": "EMP-9003",
            "role": "TEAM_MEMBER",
        },
        headers=auth_header(admin),
    )

    assert response.status_code == 422


def test_invalid_role_is_rejected(client: TestClient, make_user, auth_header):
    admin, _ = make_user(role=Role.ADMIN)

    response = client.post(
        "/api/users",
        json={
            "employeeName": "Bad Role Person",
            "employeeMailId": "badrole@example.com",
            "employeeId": "EMP-9004",
            "password": "TempPass123!",
            "role": "SUPER_ADMIN",
        },
        headers=auth_header(admin),
    )

    assert response.status_code == 422
