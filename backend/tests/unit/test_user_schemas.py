"""Unit tests for User Story 9's request schemas (backend/app/schemas/user.py) in
isolation - no DB, no FastAPI TestClient. These exercise the same password-policy
and role validation that produces a 422 at the API boundary, without needing a
running app to prove it.
"""

import pytest
from pydantic import ValidationError

from app.models.user import Role
from app.schemas.user import (
    ActiveUpdateRequest,
    CreateMemberRequest,
    PasswordResetRequest,
    RoleUpdateRequest,
)

# ---------- CreateMemberRequest ----------


def test_create_member_request_accepts_valid_input():
    request = CreateMemberRequest(
        employee_name="Priya Nair",
        employee_mail_id="priya@example.com",
        employee_id="EMP-1077",
        password="TempPass123!",
        role=Role.TEAM_MEMBER,
    )
    assert request.employee_name == "Priya Nair"
    assert request.role == Role.TEAM_MEMBER


def test_create_member_request_populates_from_a_camelcase_api_payload():
    request = CreateMemberRequest.model_validate(
        {
            "employeeName": "Priya Nair",
            "employeeMailId": "priya@example.com",
            "employeeId": "EMP-1077",
            "password": "TempPass123!",
            "role": "ADMIN",
        }
    )
    assert request.employee_mail_id == "priya@example.com"
    assert request.role == Role.ADMIN


def test_create_member_request_rejects_a_password_shorter_than_8_characters():
    with pytest.raises(ValidationError):
        CreateMemberRequest(
            employee_name="Priya Nair",
            employee_mail_id="priya@example.com",
            employee_id="EMP-1077",
            password="short",
            role=Role.TEAM_MEMBER,
        )


def test_create_member_request_rejects_a_role_outside_admin_or_team_member():
    with pytest.raises(ValidationError):
        CreateMemberRequest.model_validate(
            {
                "employeeName": "Priya Nair",
                "employeeMailId": "priya@example.com",
                "employeeId": "EMP-1077",
                "password": "TempPass123!",
                "role": "SUPER_ADMIN",
            }
        )


@pytest.mark.parametrize(
    "missing_field",
    ["employee_name", "employee_mail_id", "employee_id", "password", "role"],
)
def test_create_member_request_rejects_a_missing_required_field(missing_field):
    fields = {
        "employee_name": "Priya Nair",
        "employee_mail_id": "priya@example.com",
        "employee_id": "EMP-1077",
        "password": "TempPass123!",
        "role": Role.TEAM_MEMBER,
    }
    del fields[missing_field]
    with pytest.raises(ValidationError):
        CreateMemberRequest(**fields)


# ---------- RoleUpdateRequest ----------


@pytest.mark.parametrize("role", [Role.ADMIN, Role.TEAM_MEMBER])
def test_role_update_request_accepts_each_defined_role(role):
    request = RoleUpdateRequest(role=role)
    assert request.role == role


def test_role_update_request_rejects_an_undefined_role():
    with pytest.raises(ValidationError):
        RoleUpdateRequest.model_validate({"role": "SUPER_ADMIN"})


# ---------- PasswordResetRequest ----------


def test_password_reset_request_accepts_a_password_at_the_minimum_length():
    request = PasswordResetRequest(password="8chars!!")
    assert request.password == "8chars!!"


def test_password_reset_request_rejects_a_password_shorter_than_8_characters():
    with pytest.raises(ValidationError):
        PasswordResetRequest(password="short")


def test_password_reset_request_rejects_an_empty_password():
    with pytest.raises(ValidationError):
        PasswordResetRequest(password="")


# ---------- ActiveUpdateRequest ----------


def test_active_update_request_populates_from_a_camelcase_api_payload():
    deactivate = ActiveUpdateRequest.model_validate({"isActive": False})
    reactivate = ActiveUpdateRequest.model_validate({"isActive": True})
    assert deactivate.is_active is False
    assert reactivate.is_active is True


def test_active_update_request_rejects_a_non_boolean_value():
    with pytest.raises(ValidationError):
        ActiveUpdateRequest.model_validate({"isActive": "not-a-boolean"})
