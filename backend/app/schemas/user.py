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
