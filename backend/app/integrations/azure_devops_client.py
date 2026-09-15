from dataclasses import dataclass

import httpx

from app.core.config import Settings, get_settings

_SUPPORTED_TYPES = ("Story", "Feature")


@dataclass
class AdoWorkItem:
    id: int
    title: str
    type: str


class AzureDevOpsClient:
    """Thin, read-only wrapper around the Azure DevOps REST API.

    Every method swallows connectivity/auth/lookup failures and returns an
    empty result instead of raising, so MAT stays usable when Azure DevOps is
    unreachable or unconfigured (FR-033) — there is deliberately no method
    that creates or updates a work item (FR-031).
    """

    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()

    def _is_configured(self) -> bool:
        s = self._settings
        return bool(s.azure_devops_org_url and s.azure_devops_project and s.azure_devops_pat)

    def get(self, work_item_id: int) -> AdoWorkItem | None:
        if not self._is_configured():
            return None
        try:
            url = (
                f"{self._settings.azure_devops_org_url.rstrip('/')}/"
                f"{self._settings.azure_devops_project}/_apis/wit/workitems/{work_item_id}"
            )
            response = httpx.get(
                url,
                params={"api-version": "7.0"},
                auth=("", self._settings.azure_devops_pat),
                timeout=5.0,
            )
            if response.status_code != 200:
                return None
            fields = response.json().get("fields", {})
            work_item_type = fields.get("System.WorkItemType")
            if work_item_type not in _SUPPORTED_TYPES:
                return None
            return AdoWorkItem(
                id=work_item_id,
                title=fields.get("System.Title", ""),
                type=work_item_type,
            )
        except (httpx.HTTPError, ValueError):
            return None

    def search(self, query: str) -> list[AdoWorkItem]:
        """Suggestions for the "@<digits>" dropdown, scoped to Stories/Features.

        Azure DevOps has no prefix search over numeric work item IDs without
        the (optional) Search extension, so this resolves the typed digits as
        a direct work item ID lookup rather than a true prefix search.
        """
        if not self._is_configured() or not query or not query.isdigit():
            return []
        item = self.get(int(query))
        return [item] if item is not None else []


def get_azure_devops_client() -> AzureDevOpsClient:
    return AzureDevOpsClient()
