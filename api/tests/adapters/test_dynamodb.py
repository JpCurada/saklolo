"""DynamoDB stores against moto's in-process DynamoDB: no AWS account, no cost."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import boto3
import pytest
from moto import mock_aws

from saklolo.adapters.dynamodb import DynamoCaseStore, DynamoDispatchStore
from saklolo.adapters.outbox import InMemoryOutbox
from saklolo.config import Settings
from saklolo.dispatch.models import (
    CaseAction,
    CaseEvent,
    CaseStatus,
    DispatchRecord,
    MessageRecord,
    ReceiveKind,
)
from saklolo.dispatch.service import DispatchService
from saklolo.domain.cases import Case
from saklolo.domain.models import (
    Channel,
    ExtractedRequest,
    InboundMessage,
    Location,
    LocationSource,
    TriageDecision,
)
from saklolo.handlers.wiring import dynamo_stores
from tests.agents.fakes import FakeStructuredModel, fake_deps
from tests.dispatch.test_service import decision_for, extraction_for

NOW = datetime(2026, 11, 10, 1, 30, tzinfo=UTC)


@pytest.fixture
def dynamodb(monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.setenv(name, "testing")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    with mock_aws():
        resource = boto3.resource("dynamodb", region_name="ap-southeast-1")
        for name, key in (
            ("cases", "case_id"),
            ("messages", "message_id"),
            ("dispatch", "case_id"),
        ):
            resource.create_table(
                TableName=name,
                KeySchema=[{"AttributeName": key, "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": key, "AttributeType": "S"}],
                BillingMode="PAY_PER_REQUEST",
            )
        yield resource


def case(case_id: str, last_seen: datetime = NOW, closed: bool = False) -> Case:
    return Case(
        case_id=case_id,
        senders={"+639000000002", "+639000000103"},
        location=Location(barangay="Malanday", lat=14.663, lng=121.1, source=LocationSource.TEXT),
        embedding=[0.125, -0.5, 0.333],
        opened_at=NOW,
        last_seen=last_seen,
        closed=closed,
    )


def test_a_case_round_trips_exactly(dynamodb: Any) -> None:
    store = DynamoCaseStore(dynamodb.Table("cases"))

    store.save(case("case-0001"))

    assert store.get("case-0001") == case("case-0001")
    assert store.get("case-9999") is None


def test_open_cases_skips_closed_and_old_ones(dynamodb: Any) -> None:
    store = DynamoCaseStore(dynamodb.Table("cases"))
    store.save(case("case-0001"))
    store.save(case("case-0002", closed=True))
    store.save(case("case-0003", last_seen=NOW - timedelta(days=2)))
    store.next_id()  # the counter item must never show up as a case

    open_ids = [c.case_id for c in store.open_cases(since=NOW - timedelta(hours=12))]

    assert open_ids == ["case-0001"]


def test_case_numbers_keep_counting_across_restarts(dynamodb: Any) -> None:
    first = DynamoCaseStore(dynamodb.Table("cases"))
    assert [first.next_id(), first.next_id()] == ["case-0001", "case-0002"]

    restarted = DynamoCaseStore(dynamodb.Table("cases"))

    assert restarted.next_id() == "case-0003"


def test_messages_come_back_in_arrival_order(dynamodb: Any) -> None:
    store = DynamoDispatchStore(dynamodb.Table("messages"), dynamodb.Table("dispatch"))
    later_storm_time = message("m1", NOW + timedelta(hours=1))
    earlier_storm_time = message("m2", NOW)

    store.add_message(later_storm_time)
    store.add_message(earlier_storm_time)

    assert [m.message_id for m in store.messages()] == ["m1", "m2"]
    assert store.messages()[0] == later_storm_time


def test_decisions_and_their_history_survive_a_restart(dynamodb: Any) -> None:
    tables = dynamodb.Table("messages"), dynamodb.Table("dispatch")
    record = DispatchRecord(
        status=CaseStatus.CLOSED,
        assigned_team="Team Bravo",
        history=[
            CaseEvent(action=CaseAction.CLOSED, dispatcher="Ana", at=NOW, detail="Confirmed safe")
        ],
    )
    DynamoDispatchStore(*tables).save_record("case-0001", record)

    restarted = DynamoDispatchStore(*tables)

    assert restarted.case_ids() == ["case-0001"]
    assert restarted.record("case-0001") == record
    assert restarted.record("case-9999") is None


def message(message_id: str, received_at: datetime) -> MessageRecord:
    return MessageRecord(
        message_id=message_id,
        message=InboundMessage(
            sender="+639000000002",
            text="nasa bubong kami",
            channel=Channel.SMS,
            received_at=received_at,
        ),
        kind=ReceiveKind.TRIAGED,
        outcome=None,
        case_id="case-0001",
    )


def test_the_queue_and_its_history_survive_an_api_restart(dynamodb: Any) -> None:
    def start() -> DispatchService:
        model = FakeStructuredModel(
            {ExtractedRequest: extraction_for, TriageDecision: decision_for}
        )
        cases = DynamoCaseStore(dynamodb.Table("cases"))
        store = DynamoDispatchStore(dynamodb.Table("messages"), dynamodb.Table("dispatch"))
        return DispatchService(fake_deps(model, cases=cases), InMemoryOutbox(), store)

    before = start()
    before.receive(
        InboundMessage(
            sender="+639000000001", text="nasa bubong kami", channel=Channel.SMS, received_at=NOW
        )
    )
    [opened] = before.cases()
    before.assign(opened.case_id, "Team Bravo", "Ana")

    [after] = start().cases()

    assert after.case_id == opened.case_id
    assert after.assigned_team == "Team Bravo"
    assert [(e.action, e.dispatcher) for e in after.history] == [(CaseAction.ASSIGNED, "Ana")]
    assert len(after.sources) == 1


def test_tables_are_all_or_nothing() -> None:
    assert dynamo_stores(Settings(cases_table="", messages_table="", dispatch_table="")) is None
    with pytest.raises(ValueError, match="all of"):
        dynamo_stores(Settings(cases_table="c", messages_table="", dispatch_table=""))
