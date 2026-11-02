"""DynamoDB stores, so cases and dispatcher decisions survive an API restart.

Each item keeps its object as one JSON `body` attribute: DynamoDB would otherwise
turn every float of a case's embedding into a Decimal. The few attributes that are
filtered on are also stored on their own.

Listing uses Scan. That's fine for a city's storm (thousands of items); a larger
deployment would add a GSI on status and last_seen.
"""

import json
import time
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

from botocore.exceptions import ClientError

from saklolo.dispatch.models import DispatchRecord, MessageRecord, ReplayStatus
from saklolo.domain.cases import Case
from saklolo.domain.errors import CaseClosedError
from saklolo.domain.models import Location, OutboundMessage

# Two items in the cases table aren't cases: the case-number counter and the replay
# in progress. Neither has a `closed` attribute, so open_cases never returns them.
COUNTER_KEY = "#counter"
REPLAY_KEY = "#replay"


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


def _case_from_item(item: dict[str, Any]) -> Case:
    data = json.loads(item["body"])
    return Case(
        case_id=data["case_id"],
        senders=set(data["senders"]),
        location=Location.model_validate(data["location"]),
        embedding=data["embedding"],
        opened_at=datetime.fromisoformat(data["opened_at"]),
        last_seen=datetime.fromisoformat(data["last_seen"]),
        closed=item["closed"],  # close() sets only this attribute
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
        return [_case_from_item(item) for item in items]

    def get(self, case_id: str) -> Case | None:
        item = self._table.get_item(Key={"case_id": case_id}).get("Item")
        return _case_from_item(item) if item and "body" in item else None

    def save(self, case: Case) -> None:
        try:
            self._table.put_item(
                Item={
                    "case_id": case.case_id,
                    "closed": case.closed,
                    "last_seen": case.last_seen.isoformat(),
                    "body": _case_to_json(case),
                },
                # The API closes cases while the worker saves them: never reopen one.
                ConditionExpression="attribute_not_exists(case_id) OR closed = :no",
                ExpressionAttributeValues={":no": False},
            )
        except ClientError as error:
            if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise CaseClosedError(case.case_id) from error
            raise

    def close(self, case_id: str) -> None:
        self._table.update_item(
            Key={"case_id": case_id},
            UpdateExpression="SET closed = :yes",
            ExpressionAttributeValues={":yes": True},
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
        self._last_ns = 0

    def add_message(self, record: MessageRecord) -> None:
        # The clock can repeat (Windows' is coarse); keep this process's order strict.
        self._last_ns = max(time.time_ns(), self._last_ns + 1)
        self._messages.put_item(
            Item={
                "message_id": record.message_id,
                # Arrival order: a replay's received_at can be earlier than a live message's.
                "stored_at": self._last_ns,
                "body": record.model_dump_json(),
            }
        )

    def has_message(self, message_id: str) -> bool:
        key = {"message_id": message_id}
        return "Item" in self._messages.get_item(Key=key, ProjectionExpression="message_id")

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


class DynamoOutbox:
    """Outbox on its own table (`outbox_id`): the worker writes, the API reads."""

    def __init__(self, table: Any) -> None:
        self._table = table
        self._last_ns = 0

    def send_text(self, recipient: str, body: str) -> None:
        sent = OutboundMessage(recipient=recipient, body=body, sent_at=datetime.now(UTC))
        # The clock can repeat (Windows' is coarse), and a resident's replies must not swap.
        self._last_ns = max(time.time_ns(), self._last_ns + 1)
        self._table.put_item(
            Item={
                "outbox_id": uuid.uuid4().hex,
                "recipient": recipient,
                "stored_at": self._last_ns,
                "body": sent.model_dump_json(),
            }
        )

    def sent(self, recipient: str | None = None) -> list[OutboundMessage]:
        kwargs: dict[str, Any] = {}
        if recipient is not None:
            kwargs = {
                "FilterExpression": "recipient = :r",
                "ExpressionAttributeValues": {":r": recipient},
            }
        items = sorted(_scan(self._table, **kwargs), key=lambda item: int(item["stored_at"]))
        return [OutboundMessage.model_validate_json(item["body"]) for item in items]


class DynamoReplayState:
    """The one replay in progress, as a single item in the cases table."""

    def __init__(self, table: Any) -> None:
        self._table = table

    def _item(self) -> dict[str, Any] | None:
        response = self._table.get_item(Key={"case_id": REPLAY_KEY}, ConsistentRead=True)
        item: dict[str, Any] | None = response.get("Item")
        return item

    def status(self) -> ReplayStatus:
        item = self._item()
        if item is None:
            return ReplayStatus(running=False, split=None, sent=0, total=0)
        sent, total = int(item["sent"]), int(item["total"])
        return ReplayStatus(
            running=not item["stopped"] and sent < total,
            split=item["split"],
            sent=sent,
            total=total,
        )

    def begin(self, run_id: str, split: str, total: int) -> None:
        self._table.put_item(
            Item={
                "case_id": REPLAY_KEY,
                "run_id": run_id,
                "split": split,
                "sent": 0,
                "total": total,
                "stopped": False,
            }
        )

    def stop(self) -> None:
        if self._item() is not None:
            self._table.update_item(
                Key={"case_id": REPLAY_KEY},
                UpdateExpression="SET stopped = :yes",
                ExpressionAttributeValues={":yes": True},
            )

    def is_active(self, run_id: str) -> bool:
        item = self._item()
        return item is not None and item["run_id"] == run_id and not item["stopped"]

    def add(self, sent: int = 0, total: int = 0) -> None:
        self._table.update_item(
            Key={"case_id": REPLAY_KEY},
            UpdateExpression="ADD sent :sent, #total :total",
            ExpressionAttributeNames={"#total": "total"},
            ExpressionAttributeValues={":sent": sent, ":total": total},
        )
