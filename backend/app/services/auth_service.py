from sqlalchemy.orm import Session

from app.core.exceptions import InvalidCredentialsError, ValidationFailedError
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


def login(db: Session, employee_mail_id: str, password: str, terms_accepted: bool) -> tuple[User, str]:
    if not terms_accepted:
        raise ValidationFailedError("You must agree to the Terms and Conditions to sign in.")

    repo = UserRepository(db)
    user = repo.get_by_mail_id(employee_mail_id)
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("Employee Mail ID or Password is incorrect.")

    user = repo.mark_terms_accepted(user)
    token = create_access_token(subject=user.id)
    return user, token
