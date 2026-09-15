from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps.auth import require_role
from app.models.user import Role, User
from app.schemas.user import (
    ActiveUpdateRequest,
    CreateMemberRequest,
    PasswordResetRequest,
    RoleUpdateRequest,
    UserResponse,
)
from app.services import user_service

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
def search_users(
    q: str | None = Query(default=None),
    active_only: bool = Query(default=True, alias="activeOnly"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_role(Role.ADMIN)),
) -> list[UserResponse]:
    users = user_service.search_users(db, q, active_only)
    return [UserResponse.model_validate(user) for user in users]


@router.post("", response_model=UserResponse, status_code=201)
def create_member(
    payload: CreateMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
) -> UserResponse:
    user = user_service.create_member(
        db,
        admin=current_user,
        employee_name=payload.employee_name,
        employee_mail_id=payload.employee_mail_id,
        employee_id=payload.employee_id,
        password=payload.password,
        role=payload.role,
    )
    return UserResponse.model_validate(user)


@router.patch("/{user_id}/role", response_model=UserResponse)
def update_role(
    user_id: int,
    payload: RoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
) -> UserResponse:
    user = user_service.update_role(db, current_user, user_id, payload.role)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}/password", response_model=UserResponse)
def reset_password(
    user_id: int,
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
) -> UserResponse:
    user = user_service.reset_password(db, current_user, user_id, payload.password)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}/active", response_model=UserResponse)
def set_active(
    user_id: int,
    payload: ActiveUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
) -> UserResponse:
    user = user_service.set_active(db, current_user, user_id, payload.is_active)
    return UserResponse.model_validate(user)
