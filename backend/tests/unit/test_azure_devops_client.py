import httpx
import pytest

from app.core.config import Settings
from app.integrations.azure_devops_client import AzureDevOpsClient


def _configured_settings() -> Settings:
    return Settings(
        azure_devops_org_url="https://dev.azure.com/example-org",
        azure_devops_project="MAT",
        azure_devops_pat="fake-pat",
    )


def _unconfigured_settings() -> Settings:
    return Settings(azure_devops_org_url="", azure_devops_project="", azure_devops_pat="")


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict:
        return self._payload


def _work_item_payload(work_item_type: str = "Story", title: str = "Implement onboarding API") -> dict:
    return {"fields": {"System.WorkItemType": work_item_type, "System.Title": title}}


# ---------- get() ----------


def test_get_returns_none_when_unconfigured(monkeypatch):
    client = AzureDevOpsClient(_unconfigured_settings())

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("httpx.get should not be called when unconfigured")

    monkeypatch.setattr("app.integrations.azure_devops_client.httpx.get", _fail_if_called)

    assert client.get(1234) is None


def test_get_returns_work_item_on_success(monkeypatch):
    client = AzureDevOpsClient(_configured_settings())
    monkeypatch.setattr(
        "app.integrations.azure_devops_client.httpx.get",
        lambda *args, **kwargs: _FakeResponse(200, _work_item_payload()),
    )

    item = client.get(1234)

    assert item is not None
    assert item.id == 1234
    assert item.title == "Implement onboarding API"
    assert item.type == "Story"


def test_get_returns_none_for_non_2xx_response(monkeypatch):
    client = AzureDevOpsClient(_configured_settings())
    monkeypatch.setattr(
        "app.integrations.azure_devops_client.httpx.get",
        lambda *args, **kwargs: _FakeResponse(404),
    )

    assert client.get(1234) is None


def test_get_returns_none_for_unsupported_work_item_type(monkeypatch):
    client = AzureDevOpsClient(_configured_settings())
    monkeypatch.setattr(
        "app.integrations.azure_devops_client.httpx.get",
        lambda *args, **kwargs: _FakeResponse(200, _work_item_payload(work_item_type="Bug")),
    )

    assert client.get(1234) is None


@pytest.mark.parametrize(
    "side_effect",
    [httpx.ConnectTimeout("timed out"), httpx.HTTPError("boom")],
)
def test_get_fails_soft_on_connectivity_errors(monkeypatch, side_effect):
    client = AzureDevOpsClient(_configured_settings())

    def _raise(*args, **kwargs):
        raise side_effect

    monkeypatch.setattr("app.integrations.azure_devops_client.httpx.get", _raise)

    assert client.get(1234) is None


# ---------- search() ----------


def test_search_returns_empty_when_unconfigured(monkeypatch):
    client = AzureDevOpsClient(_unconfigured_settings())
    monkeypatch.setattr(
        "app.integrations.azure_devops_client.httpx.get",
        lambda *args, **kwargs: _FakeResponse(200, _work_item_payload()),
    )

    assert client.search("1234") == []


def test_search_returns_empty_for_non_numeric_query(monkeypatch):
    client = AzureDevOpsClient(_configured_settings())
    monkeypatch.setattr(
        "app.integrations.azure_devops_client.httpx.get",
        lambda *args, **kwargs: _FakeResponse(200, _work_item_payload()),
    )

    assert client.search("Sarah") == []
    assert client.search("") == []


def test_search_returns_single_match_for_a_known_id(monkeypatch):
    client = AzureDevOpsClient(_configured_settings())
    monkeypatch.setattr(
        "app.integrations.azure_devops_client.httpx.get",
        lambda *args, **kwargs: _FakeResponse(200, _work_item_payload()),
    )

    results = client.search("1234")

    assert len(results) == 1
    assert results[0].id == 1234


def test_search_returns_empty_when_id_is_not_found(monkeypatch):
    client = AzureDevOpsClient(_configured_settings())
    monkeypatch.setattr(
        "app.integrations.azure_devops_client.httpx.get",
        lambda *args, **kwargs: _FakeResponse(404),
    )

    assert client.search("9999") == []
