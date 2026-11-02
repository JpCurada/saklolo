"""Where the dispatcher's side of a case lives: received messages and decisions."""

from typing import Protocol

from saklolo.dispatch.models import DispatchRecord, MessageRecord


class DispatchStore(Protocol):
    def add_message(self, record: MessageRecord) -> None: ...

    def has_message(self, message_id: str) -> bool: ...

    def messages(self) -> list[MessageRecord]:
        """Every received message, oldest first."""
        ...

    def case_ids(self) -> list[str]: ...

    def record(self, case_id: str) -> DispatchRecord | None: ...

    def save_record(self, case_id: str, record: DispatchRecord) -> None: ...


class InMemoryDispatchStore:
    """For evals, tests, and a demo without AWS tables."""

    def __init__(self) -> None:
        self._messages: list[MessageRecord] = []
        self._records: dict[str, DispatchRecord] = {}

    def add_message(self, record: MessageRecord) -> None:
        self._messages.append(record)

    def has_message(self, message_id: str) -> bool:
        return any(m.message_id == message_id for m in self._messages)

    def messages(self) -> list[MessageRecord]:
        return list(self._messages)

    def case_ids(self) -> list[str]:
        return list(self._records)

    def record(self, case_id: str) -> DispatchRecord | None:
        stored = self._records.get(case_id)
        return stored.model_copy(deep=True) if stored else None

    def save_record(self, case_id: str, record: DispatchRecord) -> None:
        self._records[case_id] = record.model_copy(deep=True)
