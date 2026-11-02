"""DynamoDB stores, so cases and dispatcher decisions survive an API restart.

Each item keeps its object as one JSON `body` attribute: DynamoDB would otherwise
turn every float of a case's embedding into a Decimal. The few attributes that are
filtered on are also stored on their own.

Listing uses Scan. That's fine for a city's storm (thousands of items); a larger
deployment would add a GSI on status and last_seen.
"""

import json
import time
from collections.abc import Iterator
from datetime import datetime
from typing import Any

from saklolo.dispatch.models import DispatchRecord, MessageRecord
from saklolo.domain.cases import Case
from saklolo.domain.models import Location

# One item in the cases table holds the case-number counter.
COUNTER_KEY = "#counter"


def _scan(table: Any, **kwargs: Any) -> Iterator[dict[str, Any]]:
    while True:
        page = table.scan(**kwargs)
        yield from page.get("Items", [])
        if "LastEvaluatedKey" not in page:
            return
        kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]


def _case_to_json(case: Case) -> str:
    return json.dumps(
        {
            "case_id": case.case_id,
            "senders": sorted(case.senders),
            "location": case.location.model_dump(mode="json"),
            "embedding": case.embedding,
            "opened_at": case.opened_at.isoformat(),
            "last_seen": case.last_seen.isoformat(),
            "closed": case.closed,
            "reported_safe": case.reported_safe,
            "message_count": case.message_count,
        }
    )


def _case_from_json(body: str) -> Case:
    data = json.loads(body)
    return Case(
        case_id=data["case_id"],
        senders=set(data["senders"]),
        location=Location.model_validate(data["location"]),
        embedding=data["embedding"],
        opened_at=datetime.fromisoformat(data["opened_at"]),
        last_seen=datetime.fromisoformat(data["last_seen"]),
        closed=data["closed"],
        reported_safe=data["reported_safe"],
        message_count=data["message_count"],
    )


class DynamoCaseStore:
    """CaseStore on the cases table (hash key `case_id`)."""

    def __init__(self, table: Any) -> None:
        self._table = table

    def open_cases(self, since: datetime) -> list[Case]:
        items = _scan(
            self._table,
            FilterExpression="closed = :no AND last_seen >= :since",
            ExpressionAttributeValues={":no": False, ":since": since.isoformat()},
        )
        return [_case_from_json(item["body"]) for item in items]

    def get(self, case_id: str) -> Case | None:
        item = self._table.get_item(Key={"case_id": case_id}).get("Item")
        return _case_from_json(item["body"]) if item and "body" in item else None

    def save(self, case: Case) -> None:
        self._table.put_item(
            Item={
                "case_id": case.case_id,
                "closed": case.closed,
                "last_seen": case.last_seen.isoformat(),
                "body": _case_to_json(case),
            }
        )

    def next_id(self) -> str:
        """Atomic, so two API processes never hand out the same number."""
        updated = self._table.update_item(
            Key={"case_id": COUNTER_KEY},
            UpdateExpression="ADD next_number :one",
            ExpressionAttributeValues={":one": 1},
            ReturnValues="UPDATED_NEW",
        )
        return f"case-{int(updated['Attributes']['next_number']):04d}"


class DynamoDispatchStore:
    """DispatchStore on the messages table (`message_id`) and dispatch table (`case_id`)."""

    def __init__(self, messages_table: Any, dispatch_table: Any) -> None:
        self._messages = messages_table
        self._dispatch = dispatch_table

    def add_message(self, record: MessageRecord) -> None:
        self._messages.put_item(
            Item={
                "message_id": record.message_id,
                # Arrival order: a replay's received_at can be earlier than a live message's.
                "stored_at": time.time_ns(),
                "body": record.model_dump_json(),
            }
        )

    def messages(self) -> list[MessageRecord]:
        items = sorted(_scan(self._messages), key=lambda item: int(item["stored_at"]))
        return [MessageRecord.model_validate_json(item["body"]) for item in items]

    def case_ids(self) -> list[str]:
        items = _scan(self._dispatch, ProjectionExpression="case_id")
        return sorted(item["case_id"] for item in items)

    def record(self, case_id: str) -> DispatchRecord | None:
        item = self._dispatch.get_item(Key={"case_id": case_id}).get("Item")
        return DispatchRecord.model_validate_json(item["body"]) if item else None

    def save_record(self, case_id: str, record: DispatchRecord) -> None:
        self._dispatch.put_item(Item={"case_id": case_id, "body": record.model_dump_json()})
