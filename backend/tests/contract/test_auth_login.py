from fastapi.testclient import TestClient

from app.models.user import Role


def test_login_with_valid_credentials_returns_token_and_user(client: TestClient, make_user):
    user, password = make_user(role=Role.TEAM_MEMBER)

    response = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": user.employee_mail_id,
            "password": password,
            "termsAccepted": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["accessToken"]
    assert body["user"]["employeeMailId"] == user.employee_mail_id
    assert body["user"]["role"] == "TEAM_MEMBER"


def test_login_with_wrong_password_is_rejected(client: TestClient, make_user):
    user, _password = make_user()

    response = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": user.employee_mail_id,
            "password": "wrong-password",
            "termsAccepted": True,
        },
    )

    assert response.status_code == 401


def test_login_with_unknown_mail_id_is_rejected(client: TestClient):
    response = client.post(
        "/api/auth/login",
        json={"employeeMailId": "nobody@example.com", "password": "whatever", "termsAccepted": True},
    )

    assert response.status_code == 401


def test_login_for_deactivated_user_is_rejected(client: TestClient, make_user):
    user, password = make_user(is_active=False)

    response = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": user.employee_mail_id,
            "password": password,
            "termsAccepted": True,
        },
    )

    assert response.status_code == 401


def test_login_result_is_the_same_regardless_of_which_sign_in_option_was_clicked(
    client: TestClient, make_user
):
    admin, password = make_user(role=Role.ADMIN)

    response = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": admin.employee_mail_id,
            "password": password,
            "termsAccepted": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "ADMIN"


def test_login_without_accepting_terms_is_rejected(client: TestClient, make_user):
    user, password = make_user()

    response = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": user.employee_mail_id,
            "password": password,
            "termsAccepted": False,
        },
    )

    assert response.status_code == 422


def test_login_missing_terms_accepted_field_is_rejected(client: TestClient, make_user):
    user, password = make_user()

    response = client.post(
        "/api/auth/login",
        json={"employeeMailId": user.employee_mail_id, "password": password},
    )

    assert response.status_code == 422


def test_login_records_terms_acceptance_on_the_account(client: TestClient, make_user, auth_header):
    user, password = make_user()

    login_response = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": user.employee_mail_id,
            "password": password,
            "termsAccepted": True,
        },
    )
    assert login_response.status_code == 200
    assert login_response.json()["user"]["termsAccepted"] is True

    me_response = client.get("/api/auth/me", headers=auth_header(user))
    assert me_response.json()["termsAccepted"] is True
