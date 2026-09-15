"""Unit tests for User Story 10's response schema (backend/app/schemas/activity_log.py)
in isolation - no DB, no FastAPI TestClient. These exercise the camelCase
serialization contract (activity-log-api.md) that the endpoint relies on,
without needing a running app to prove it.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.activity_log import ActivityLogEntryResponse


def _fields(**overrides):
    fields = {
        "id": 901,
        "actor_id": 3,
        "actor_name": "John Admin",
        "action": "MEETING_DELETED",
        "entity_type": "Meeting",
        "entity_id": 12,
        "timestamp": datetime(2026, 9, 14, 11, 5, 0, tzinfo=timezone.utc),
    }
    fields.update(overrides)
    return fields


def test_accepts_valid_input_via_snake_case_field_names():
    entry = ActivityLogEntryResponse(**_fields())
    assert entry.actor_id == 3
    assert entry.action == "MEETING_DELETED"


def test_serializes_to_the_camelcase_shape_the_contract_specifies():
    entry = ActivityLogEntryResponse(**_fields())
    dumped = entry.model_dump(by_alias=True, mode="json")
    assert set(dumped.keys()) == {
        "id",
        "actorId",
        "actorName",
        "action",
        "entityType",
        "entityId",
        "timestamp",
    }
    assert dumped["actorId"] == 3
    assert dumped["entityType"] == "Meeting"


def test_parses_an_iso_timestamp_string_into_a_datetime():
    entry = ActivityLogEntryResponse.model_validate(
        {
            "id": 901,
            "actorId": 3,
            "actorName": "John Admin",
            "action": "MEETING_DELETED",
            "entityType": "Meeting",
            "entityId": 12,
            "timestamp": "2026-09-14T11:05:00Z",
        }
    )
    assert entry.timestamp == datetime(2026, 9, 14, 11, 5, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "missing_field",
    ["id", "actor_id", "actor_name", "action", "entity_type", "entity_id", "timestamp"],
)
def test_rejects_a_missing_required_field(missing_field):
    fields = _fields()
    del fields[missing_field]
    with pytest.raises(ValidationError):
        ActivityLogEntryResponse(**fields)


@pytest.mark.parametrize("field", ["id", "actor_id", "entity_id"])
def test_rejects_a_non_integer_id_field(field):
    with pytest.raises(ValidationError):
        ActivityLogEntryResponse(**_fields(**{field: "not-a-number"}))


def test_rejects_an_unparseable_timestamp():
    with pytest.raises(ValidationError):
        ActivityLogEntryResponse(**_fields(timestamp="not-a-timestamp"))
