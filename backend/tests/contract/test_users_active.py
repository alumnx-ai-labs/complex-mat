from fastapi.testclient import TestClient

from app.models.user import Role


def test_deactivating_a_member_blocks_sign_in_and_excludes_them_from_search(
    client: TestClient, make_user, auth_header
):
    admin, _ = make_user(role=Role.ADMIN)
    member, password = make_user(role=Role.TEAM_MEMBER)

    response = client.patch(
        f"/api/users/{member.id}/active",
        json={"isActive": False},
        headers=auth_header(admin),
    )
    assert response.status_code == 200
    assert response.json()["isActive"] is False

    login = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": member.employee_mail_id,
            "password": password,
            "termsAccepted": True,
        },
    )
    assert login.status_code == 401

    search = client.get(
        "/api/users", params={"q": member.employee_name}, headers=auth_header(admin)
    )
    ids = {u["id"] for u in search.json()}
    assert member.id not in ids


def test_reactivating_a_member_restores_sign_in_and_search_visibility(
    client: TestClient, make_user, auth_header
):
    admin, _ = make_user(role=Role.ADMIN)
    member, password = make_user(role=Role.TEAM_MEMBER, is_active=False)

    response = client.patch(
        f"/api/users/{member.id}/active",
        json={"isActive": True},
        headers=auth_header(admin),
    )
    assert response.status_code == 200
    assert response.json()["isActive"] is True

    login = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": member.employee_mail_id,
            "password": password,
            "termsAccepted": True,
        },
    )
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "TEAM_MEMBER"

    search = client.get(
        "/api/users", params={"q": member.employee_name}, headers=auth_header(admin)
    )
    ids = {u["id"] for u in search.json()}
    assert member.id in ids


def test_team_member_cannot_deactivate_anyone(client: TestClient, make_user, auth_header):
    member, _ = make_user(role=Role.TEAM_MEMBER)
    other, _ = make_user(role=Role.TEAM_MEMBER)

    response = client.patch(
        f"/api/users/{other.id}/active",
        json={"isActive": False},
        headers=auth_header(member),
    )

    assert response.status_code == 403


def test_active_update_on_unknown_user_returns_404(client: TestClient, make_user, auth_header):
    admin, _ = make_user(role=Role.ADMIN)

    response = client.patch(
        "/api/users/999999/active",
        json={"isActive": False},
        headers=auth_header(admin),
    )

    assert response.status_code == 404
