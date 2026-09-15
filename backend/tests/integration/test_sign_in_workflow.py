"""Integration coverage for User Story 1 - Sign In and Reach the Shared Workspace
(spec.md Acceptance Scenarios 1-7), exercising the login/me endpoints together
across roles rather than one endpoint in isolation.

AC3/AC4 (Role-gated navigation) are a frontend concern, covered by
frontend/tests/integration/roleGating.test.tsx - this file covers everything
that's testable at the API boundary.
"""

from app.models.user import Role


def test_admin_creates_accounts_and_each_signs_in_with_their_own_stored_role(
    client, make_user, auth_header
):
    """Independent Test (spec.md US1) + AC1: sign-in resolves to the account's
    actual stored Role, regardless of which sign-in option (Team Member/Admin)
    was used to submit the same credentials - the frontend option clicked is
    never sent to the backend, only the credentials themselves."""
    team_member, team_member_password = make_user(role=Role.TEAM_MEMBER)
    admin, admin_password = make_user(role=Role.ADMIN)

    team_member_login = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": team_member.employee_mail_id,
            "password": team_member_password,
            "termsAccepted": True,
        },
    )
    assert team_member_login.status_code == 200
    assert team_member_login.json()["user"]["role"] == "TEAM_MEMBER"

    admin_login = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": admin.employee_mail_id,
            "password": admin_password,
            "termsAccepted": True,
        },
    )
    assert admin_login.status_code == 200
    assert admin_login.json()["user"]["role"] == "ADMIN"

    # Admin-only search stays gated by the account's actual Role (AC3/AC4's
    # backend-enforced half - the frontend nav gate is the other half).
    team_member_token = {"Authorization": f"Bearer {team_member_login.json()['accessToken']}"}
    admin_token = {"Authorization": f"Bearer {admin_login.json()['accessToken']}"}
    assert client.get("/api/users", headers=team_member_token).status_code == 403
    assert client.get("/api/users", headers=admin_token).status_code == 200


def test_wrong_password_and_deactivated_account_are_both_rejected_as_incorrect_credentials(
    client, make_user
):
    """AC2: neither a wrong password nor a deactivated account signs anyone
    in; both fail the same way, without revealing which condition applied."""
    user, password = make_user()
    deactivated, deactivated_password = make_user(is_active=False)

    wrong_password = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": user.employee_mail_id,
            "password": "not-the-real-password",
            "termsAccepted": True,
        },
    )
    assert wrong_password.status_code == 401

    deactivated_login = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": deactivated.employee_mail_id,
            "password": deactivated_password,
            "termsAccepted": True,
        },
    )
    assert deactivated_login.status_code == 401
    assert wrong_password.json()["detail"] == deactivated_login.json()["detail"]


def test_there_is_no_self_registration_endpoint(client):
    """AC5: every account is created only via an Admin's "Add Member" action
    - there is no sign-up/self-registration path on the API at all."""
    response = client.post(
        "/api/auth/register",
        json={
            "employeeName": "New Person",
            "employeeMailId": "new.person@example.com",
            "password": "Password123!",
        },
    )
    assert response.status_code == 404


def test_sign_in_is_rejected_and_terms_are_not_recorded_when_the_checkbox_is_unchecked(
    client, make_user, auth_header
):
    """AC6: the Login screen disables Sign In client-side until the Terms
    and Conditions checkbox is checked; the backend independently enforces
    the same rule, rejecting a submission where termsAccepted is false or
    missing, and never recording acceptance for a rejected attempt."""
    user, password = make_user()

    unchecked = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": user.employee_mail_id,
            "password": password,
            "termsAccepted": False,
        },
    )
    assert unchecked.status_code == 422

    missing_field = client.post(
        "/api/auth/login",
        json={"employeeMailId": user.employee_mail_id, "password": password},
    )
    assert missing_field.status_code == 422

    # Neither rejected attempt recorded acceptance on the account.
    still_pending = client.get("/api/auth/me", headers=auth_header(user))
    assert still_pending.json()["termsAccepted"] is False


def test_successful_sign_in_records_terms_acceptance_permanently_on_the_account(
    client, make_user, auth_header
):
    """AC7: checking the box and signing in successfully records Terms
    acceptance on the account - and it stays recorded on later sessions,
    not just the response from the sign-in call itself."""
    user, password = make_user()

    login = client.post(
        "/api/auth/login",
        json={
            "employeeMailId": user.employee_mail_id,
            "password": password,
            "termsAccepted": True,
        },
    )
    assert login.status_code == 200
    assert login.json()["user"]["termsAccepted"] is True

    # A later, independent session (e.g. after a refresh) still sees it recorded.
    later_session = client.get("/api/auth/me", headers=auth_header(user))
    assert later_session.status_code == 200
    assert later_session.json()["termsAccepted"] is True
