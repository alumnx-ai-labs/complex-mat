from fastapi.testclient import TestClient

from app.models.user import Role


def test_me_with_valid_token_returns_current_user(client: TestClient, make_user, auth_header):
    user, _password = make_user(role=Role.ADMIN)

    response = client.get("/api/auth/me", headers=auth_header(user))

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == user.id
    assert body["employeeMailId"] == user.employee_mail_id
    assert body["role"] == "ADMIN"
    assert body["termsAccepted"] is False


def test_me_without_token_is_rejected(client: TestClient):
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_me_with_invalid_token_is_rejected(client: TestClient):
    response = client.get(
        "/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401


def test_me_for_deactivated_user_is_rejected(client: TestClient, make_user, auth_header):
    user, _password = make_user(is_active=False)

    response = client.get("/api/auth/me", headers=auth_header(user))

    assert response.status_code == 401
