from app.schemas.camel import CamelModel
from app.schemas.user import UserResponse


class LoginRequest(CamelModel):
    employee_mail_id: str
    password: str
    terms_accepted: bool


class LoginResponse(CamelModel):
    access_token: str
    user: UserResponse
