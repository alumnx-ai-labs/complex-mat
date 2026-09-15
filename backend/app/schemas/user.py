from pydantic import Field

from app.models.user import Role
from app.schemas.camel import CamelModel


class UserResponse(CamelModel):
    id: int
    employee_name: str
    employee_mail_id: str
    employee_id: str
    role: Role
    is_active: bool
    terms_accepted: bool

    model_config = CamelModel.model_config | {"from_attributes": True}


class CreateMemberRequest(CamelModel):
    employee_name: str
    employee_mail_id: str
    employee_id: str
    password: str = Field(min_length=8)
    role: Role


class RoleUpdateRequest(CamelModel):
    role: Role


class PasswordResetRequest(CamelModel):
    password: str = Field(min_length=8)


class ActiveUpdateRequest(CamelModel):
    is_active: bool
