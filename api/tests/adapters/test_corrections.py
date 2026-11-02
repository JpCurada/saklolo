"""Correction memory: the in-memory matcher and the AgentCore calls, with a fake client."""

import json
from typing import Any

import pytest
from botocore.exceptions import ClientError

from saklolo.adapters.corrections import (
    NAMESPACE,
    AgentCoreCorrectionMemory,
    InMemoryCorrectionMemory,
)
from saklolo.domain.errors import ServiceUnavailableError
from saklolo.domain.models import Priority
from saklolo.domain.ports import PastCorrection

ROOF = PastCorrection(
    "Family on a roof deck in Tumana", Priority.CRITICAL, Priority.HIGH, "Safe deck"
)


def test_in_memory_finds_similar_cases_only() -> None:
    memory = InMemoryCorrectionMemory()
    memory.remember(ROOF)

    assert memory.similar("Family on a roof in Malanday") == [ROOF]
    assert memory.similar("Blankets needed") == []


class FakeClient:
    def __init__(self, records: list[dict[str, Any]] | None = None, fail: bool = False) -> None:
        self.records = records or []
        self.fail = fail
        self.written: list[dict[str, Any]] = []
        self.searches: list[dict[str, Any]] = []

    def batch_create_memory_records(self, **kwargs: Any) -> dict[str, Any]:
        self.written.append(kwargs)
        return {}

    def retrieve_memory_records(self, **kwargs: Any) -> dict[str, Any]:
        if self.fail:
            raise ClientError({"Error": {"Code": "Throttled", "Message": "x"}}, "Retrieve")
        self.searches.append(kwargs)
        return {"memoryRecordSummaries": self.records}


def test_a_correction_round_trips_through_agentcore_records() -> None:
    client = FakeClient()
    memory = AgentCoreCorrectionMemory(client, "mem-1", "strategy-1")

    memory.remember(ROOF)

    [call] = client.written
    [record] = call["records"]
    assert call["memoryId"] == "mem-1"
    assert record["namespaces"] == [NAMESPACE]
    assert record["memoryStrategyId"] == "strategy-1"
    client.records = [
        {"content": record["content"], "score": 0.43},
        {"content": record["content"], "score": 0.37},  # unrelated: below the cutoff
        {"content": {"text": "not json"}, "score": 0.9},
    ]
    assert memory.similar("Family on a roof") == [ROOF]
    assert client.searches[0]["searchCriteria"]["topK"] == 3
    assert json.loads(record["content"]["text"])["corrected"] == "P2"


def test_an_agentcore_failure_is_a_service_error() -> None:
    memory = AgentCoreCorrectionMemory(FakeClient(fail=True), "mem-1")

    with pytest.raises(ServiceUnavailableError):
        memory.similar("Family on a roof")
