from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps.auth import get_current_user
from app.integrations.azure_devops_client import AzureDevOpsClient, get_azure_devops_client
from app.models.comment import Comment, MentionSourceType
from app.models.user import User
from app.repositories.ado_reference_repository import AdoReferenceRepository
from app.repositories.comment_repository import CommentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.comment import (
    CommentAdoReferenceResponse,
    CommentCreateRequest,
    CommentMentionResponse,
    CommentResponse,
)
from app.schemas.user import UserResponse
from app.services import comment_service
from app.services.mention_parser import find_ado_ids

router = APIRouter(tags=["comments"])


def _comment_to_response(db: Session, comment: Comment) -> CommentResponse:
    user_repo = UserRepository(db)
    author = user_repo.get_by_id(comment.author_id)

    mention_rows = CommentRepository(db).list_mentions(MentionSourceType.COMMENT, comment.id)
    mentions = []
    for row in mention_rows:
        user = user_repo.get_by_id(row.mentioned_user_id)
        if user is not None:
            mentions.append(
                CommentMentionResponse(user_id=user.id, employee_name=user.employee_name)
            )

    ado_repo = AdoReferenceRepository(db)
    ado_references = []
    for ado_id in find_ado_ids(comment.message):
        ref = ado_repo.get(comment.task_id, ado_id)
        if ref is not None:
            ado_references.append(
                CommentAdoReferenceResponse(
                    ado_work_item_id=ref.ado_work_item_id,
                    title=ref.cached_title,
                    type=ref.cached_type,
                    is_available=ref.is_available,
                )
            )

    return CommentResponse(
        id=comment.id,
        task_id=comment.task_id,
        author_id=comment.author_id,
        author_name=author.employee_name if author else "",
        message=comment.message,
        mentions=mentions,
        ado_references=ado_references,
        created_at=comment.created_at,
    )


@router.get("/api/tasks/{task_id}/comments", response_model=list[CommentResponse])
def list_comments(
    task_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[CommentResponse]:
    comments = comment_service.list_comments(db, task_id)
    return [_comment_to_response(db, comment) for comment in comments]


@router.post("/api/tasks/{task_id}/comments", response_model=CommentResponse, status_code=201)
def create_comment(
    task_id: int,
    payload: CommentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    client: AzureDevOpsClient = Depends(get_azure_devops_client),
) -> CommentResponse:
    comment = comment_service.create_comment(db, current_user, task_id, payload.message, client)
    return _comment_to_response(db, comment)


@router.get(
    "/api/meetings/{meeting_id}/attendees/mention-search",
    response_model=list[UserResponse],
)
def mention_search(
    meeting_id: int,
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[UserResponse]:
    users = comment_service.search_mention_candidates(db, meeting_id, q)
    return [UserResponse.model_validate(user) for user in users]
