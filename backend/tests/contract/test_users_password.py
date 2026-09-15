from fastapi.testclient import TestClient

from app.models.user import Role


def test_admin_can_reset_a_members_password(client: TestClient, make_user, auth_header):
    admin, _ = make_user(role=Role.ADMIN)
    member, old_password = make_user(role=Role.TEAM_MEMBER)

    response = client.patch(
        f"/api/users/{member.id}/password",
        json={"password": "NewTempPass456!"},
        headers=auth_header(admin),
    )
    assert response.status_code == 200
    assert "password" not in response.json()
    assert "passwordHash" not in response.json()

    old_login = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": member.employee_mail_id,
            "password": old_password,
            "termsAccepted": True,
        },
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": member.employee_mail_id,
            "password": "NewTempPass456!",
            "termsAccepted": True,
        },
    )
    assert new_login.status_code == 200


def test_team_member_cannot_reset_a_password(client: TestClient, make_user, auth_header):
    member, _ = make_user(role=Role.TEAM_MEMBER)
    other, _ = make_user(role=Role.TEAM_MEMBER)

    response = client.patch(
        f"/api/users/{other.id}/password",
        json={"password": "NewTempPass456!"},
        headers=auth_header(member),
    )

    assert response.status_code == 403


def test_password_reset_on_unknown_user_returns_404(client: TestClient, make_user, auth_header):
    admin, _ = make_user(role=Role.ADMIN)

    response = client.patch(
        "/api/users/999999/password",
        json={"password": "NewTempPass456!"},
        headers=auth_header(admin),
    )

    assert response.status_code == 404


def test_password_reset_rejects_a_password_that_is_too_short(
    client: TestClient, make_user, auth_header
):
    admin, _ = make_user(role=Role.ADMIN)
    member, _ = make_user(role=Role.TEAM_MEMBER)

    response = client.patch(
        f"/api/users/{member.id}/password",
        json={"password": "short"},
        headers=auth_header(admin),
    )

    assert response.status_code == 422
