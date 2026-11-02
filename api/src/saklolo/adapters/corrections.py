"""CorrectionMemory: what dispatchers corrected, so unsure cases can learn from it.

AgentCore Memory keeps corrections across restarts and finds similar ones by meaning.
The in-memory version needs no AWS: it matches on shared words, for demos and tests.
"""

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from botocore.exceptions import BotoCoreError, ClientError

from saklolo.domain.errors import ServiceUnavailableError
from saklolo.domain.models import Priority
from saklolo.domain.ports import PastCorrection

logger = logging.getLogger(__name__)

NAMESPACE = "/dispatcher-corrections"
WORD = re.compile(r"[^\W_]+")
# In a live test, the right match scored 0.43 and unrelated records 0.375 or less.
MIN_SCORE = 0.40


def _to_text(correction: PastCorrection) -> str:
    return json.dumps(
        {
            "summary": correction.summary,
            "first": correction.first_priority.value,
            "corrected": correction.corrected_priority.value,
            "reason": correction.reason,
        }
    )


def _from_text(text: str) -> PastCorrection | None:
    try:
        data = json.loads(text)
        return PastCorrection(
            summary=data["summary"],
            first_priority=Priority(data["first"]),
            corrected_priority=Priority(data["corrected"]),
            reason=data["reason"],
        )
    except (ValueError, KeyError, TypeError):
        return None  # a record this version can't read is skipped, not fatal


class InMemoryCorrectionMemory:
    def __init__(self) -> None:
        self._corrections: list[PastCorrection] = []

    def remember(self, correction: PastCorrection) -> None:
        self._corrections.append(correction)

    def similar(self, summary: str, limit: int = 3) -> list[PastCorrection]:
        words = set(WORD.findall(summary.casefold()))

        def overlap(item: PastCorrection) -> int:
            return len(words & set(WORD.findall(item.summary.casefold())))

        ranked = sorted(self._corrections, key=overlap, reverse=True)
        return [item for item in ranked[:limit] if overlap(item) > 0]


class AgentCoreCorrectionMemory:
    def __init__(self, client: Any, memory_id: str, strategy_id: str | None = None) -> None:
        self._client = client
        self._memory_id = memory_id
        self._strategy_id = strategy_id

    def remember(self, correction: PastCorrection) -> None:
        record: dict[str, Any] = {
            "requestIdentifier": uuid4().hex,
            "namespaces": [NAMESPACE],
            "content": {"text": _to_text(correction)},
            "timestamp": datetime.now(UTC),
        }
        if self._strategy_id:
            record["memoryStrategyId"] = self._strategy_id
        try:
            self._client.batch_create_memory_records(memoryId=self._memory_id, records=[record])
        except (BotoCoreError, ClientError) as error:
            raise ServiceUnavailableError(f"memory write: {type(error).__name__}") from error

    def similar(self, summary: str, limit: int = 3) -> list[PastCorrection]:
        criteria: dict[str, Any] = {"searchQuery": summary, "topK": limit}
        if self._strategy_id:
            criteria["memoryStrategyId"] = self._strategy_id
        try:
            found = self._client.retrieve_memory_records(
                memoryId=self._memory_id, namespace=NAMESPACE, searchCriteria=criteria
            )
        except (BotoCoreError, ClientError) as error:
            raise ServiceUnavailableError(f"memory read: {type(error).__name__}") from error
        corrections = [
            _from_text(item.get("content", {}).get("text", ""))
            for item in found.get("memoryRecordSummaries", [])
            if item.get("score", 0) >= MIN_SCORE
        ]
        return [item for item in corrections if item is not None]
