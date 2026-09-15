from fastapi.testclient import TestClient

from app.models.user import Role


def test_admin_can_change_a_members_role(client: TestClient, make_user, auth_header):
    admin, _ = make_user(role=Role.ADMIN)
    member, password = make_user(role=Role.TEAM_MEMBER)

    response = client.patch(
        f"/api/users/{member.id}/role",
        json={"role": "ADMIN"},
        headers=auth_header(admin),
    )

    assert response.status_code == 200
    assert response.json()["role"] == "ADMIN"

    login = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": member.employee_mail_id,
            "password": password,
            "termsAccepted": True,
        },
    )
    assert login.json()["user"]["role"] == "ADMIN"


def test_team_member_cannot_change_a_role(client: TestClient, make_user, auth_header):
    member, _ = make_user(role=Role.TEAM_MEMBER)
    other, _ = make_user(role=Role.TEAM_MEMBER)

    response = client.patch(
        f"/api/users/{other.id}/role",
        json={"role": "ADMIN"},
        headers=auth_header(member),
    )

    assert response.status_code == 403


def test_role_change_on_unknown_user_returns_404(client: TestClient, make_user, auth_header):
    admin, _ = make_user(role=Role.ADMIN)

    response = client.patch(
        "/api/users/999999/role",
        json={"role": "ADMIN"},
        headers=auth_header(admin),
    )

    assert response.status_code == 404
