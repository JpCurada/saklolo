"""In-process CaseStore for evals, demos, and tests (DynamoDB replaces it when deployed)."""

import itertools
from datetime import datetime

from saklolo.domain.cases import Case


class InMemoryCaseStore:
    def __init__(self) -> None:
        self._cases: dict[str, Case] = {}
        self._ids = itertools.count(1)

    def open_cases(self, since: datetime) -> list[Case]:
        return [c for c in self._cases.values() if not c.closed and c.last_seen >= since]

    def get(self, case_id: str) -> Case | None:
        return self._cases.get(case_id)

    def save(self, case: Case) -> None:
        self._cases[case.case_id] = case

    def next_id(self) -> str:
        return f"case-{next(self._ids):04d}"
