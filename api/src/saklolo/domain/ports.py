"""Interfaces the domain and agents depend on. Adapters implement them."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

from pydantic import BaseModel

from saklolo.domain.cases import Case
from saklolo.domain.models import InboundMessage, Location, TriageDecision


class MessageQueue(Protocol):
    def enqueue(self, message: InboundMessage) -> None: ...


class Notifier(Protocol):
    def send_text(self, recipient: str, body: str) -> None: ...


@dataclass(frozen=True)
class ModelUsage:
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class ModelCall[OutputT: BaseModel]:
    output: OutputT
    usage: ModelUsage


class StructuredModel(Protocol):
    """One model call that must return a validated instance of `output_type`."""

    def generate[OutputT: BaseModel](
        self, system_prompt: str, prompt: str, output_type: type[OutputT]
    ) -> ModelCall[OutputT]: ...


class Geocoder(Protocol):
    def geocode(self, query: str) -> Location | None:
        """A Marikina location for the place words, or None if it can't be placed."""
        ...


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class CaseStore(Protocol):
    def open_cases(self, since: datetime) -> list[Case]: ...

    def get(self, case_id: str) -> Case | None: ...

    def save(self, case: Case) -> None: ...

    def next_id(self) -> str: ...


@dataclass(frozen=True)
class PlaceLookup:
    """One place lookup a reviewer made, and what the geocoder answered."""

    query: str
    location: Location | None  # None: nothing found, or the service was down
    unavailable: bool = False


@dataclass(frozen=True)
class EscalationReview:
    """A second opinion on one low-confidence triage."""

    decision: TriageDecision | None  # None: the reviewers didn't submit one
    agents: tuple[str, ...]  # who worked on it, in handoff order
    usage: ModelUsage
    lookups: tuple[PlaceLookup, ...] = ()


class Escalation(Protocol):
    def review(self, brief: str) -> EscalationReview: ...


@dataclass(frozen=True)
class ArchiveMatch:
    """A known past-typhoon post that a new message copies."""

    archive_id: str
    posted: date
    similarity: float


class PostArchive(Protocol):
    def match(self, text: str) -> ArchiveMatch | None: ...
