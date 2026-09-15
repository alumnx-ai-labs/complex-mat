from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.deps.auth import get_current_user
from app.integrations.azure_devops_client import AzureDevOpsClient, get_azure_devops_client
from app.models.comment import TaskAdoReference
from app.models.user import User
from app.schemas.azure_devops import AdoReferenceResponse, AdoSuggestionResponse
from app.services import reference_service

router = APIRouter(tags=["azure-devops"])


def _open_url(ref: TaskAdoReference) -> str | None:
    if not ref.is_available:
        return None
    settings = get_settings()
    if not settings.azure_devops_org_url or not settings.azure_devops_project:
        return None
    return (
        f"{settings.azure_devops_org_url.rstrip('/')}/{settings.azure_devops_project}"
        f"/_workitems/edit/{ref.ado_work_item_id}"
    )


@router.get("/api/azure-devops/suggestions", response_model=list[AdoSuggestionResponse])
def get_suggestions(
    q: str = Query(...),
    _current_user: User = Depends(get_current_user),
    client: AzureDevOpsClient = Depends(get_azure_devops_client),
) -> list[AdoSuggestionResponse]:
    items = client.search(q)
    return [
        AdoSuggestionResponse(ado_work_item_id=item.id, title=item.title, type=item.type)
        for item in items
    ]


@router.get("/api/tasks/{task_id}/ado-references", response_model=list[AdoReferenceResponse])
def get_task_references(
    task_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
    client: AzureDevOpsClient = Depends(get_azure_devops_client),
) -> list[AdoReferenceResponse]:
    refs = reference_service.list_task_references(db, task_id, client)
    return [
        AdoReferenceResponse(
            ado_work_item_id=ref.ado_work_item_id,
            title=ref.cached_title,
            type=ref.cached_type,
            is_available=ref.is_available,
            open_url=_open_url(ref),
        )
        for ref in refs
    ]
