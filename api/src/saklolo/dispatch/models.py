"""What the dispatcher sees: cases, their sources, and the replies residents get."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from saklolo.domain.models import (
    Channel,
    InboundMessage,
    Location,
    OutboundMessage,
    Priority,
    TraceStep,
    TriageOutcome,
    Vulnerability,
    WaterLevel,
)

# Lower rank = more urgent. Messages without a priority sort last.
PRIORITY_RANK = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MODERATE: 2, Priority.INFO: 3}
NO_PRIORITY_RANK = len(PRIORITY_RANK)


def rank(priority: Priority | None) -> int:
    return PRIORITY_RANK[priority] if priority else NO_PRIORITY_RANK


class CaseStatus(StrEnum):
    OPEN = "open"
    ASSIGNED = "assigned"
    CLOSED = "closed"  # only after a dispatcher confirms the household is safe


class Badge(StrEnum):
    CORROBORATED = "corroborated"  # reported by 2+ different senders
    SUSPICIOUS = "suspicious"  # spam pattern or prompt injection; shown, never hidden
    REPORTED_SAFE = "reported_safe"  # resident says they're safe; dispatcher must confirm
    AWAITING_LOCATION = "awaiting_location"  # ask-back sent, no reply yet
    NEEDS_REVIEW = "needs_review"  # low-confidence triage: human review lane
    OVERRIDDEN = "overridden"  # a dispatcher set the priority


class CaseAction(StrEnum):
    ASSIGNED = "assigned"
    OVERRIDDEN = "overridden"
    CLOSED = "closed"


class CaseEvent(BaseModel):
    """One dispatcher decision, kept so every change has a named person behind it."""

    action: CaseAction
    dispatcher: str
    at: datetime
    detail: str


class DispatchRecord(BaseModel):
    """The dispatcher's decisions about one case."""

    status: CaseStatus = CaseStatus.OPEN
    assigned_team: str | None = None
    override: Priority | None = None
    override_reason: str | None = None
    history: list[CaseEvent] = Field(default_factory=list)


class ReceiveKind(StrEnum):
    TRIAGED = "triaged"  # ran through the pipeline
    LOCATION_REPLY = "location_reply"  # resumed a case waiting for its location


class MessageRecord(BaseModel):
    """One received message and what the pipeline made of it."""

    message_id: str
    message: InboundMessage
    kind: ReceiveKind
    outcome: TriageOutcome | None
    case_id: str | None
    # Set when the pipeline failed: the message stays visible for a human, never dropped.
    error: str | None = None
    # What each agent step did with this message (agents/trace.py).
    trace: list[TraceStep] = Field(default_factory=list)


class ReceiveResult(BaseModel):
    record: MessageRecord
    replies: list[OutboundMessage]


class ReceiveAck(BaseModel):
    """The intake has the message. Triage may still be running."""

    received_at: datetime


class QueuedMessage(BaseModel):
    """One message on the intake queue. The ID is set at intake, so a retry is detectable."""

    message_id: str
    message: InboundMessage
    replay_run: str | None = None
    reply_if_asked: str | None = None


class SourceView(BaseModel):
    message_id: str
    sender: str
    channel: Channel
    received_at: datetime
    text: str = Field(description="The resident's original words")
    english_summary: str | None
    priority: Priority | None
    trace: list[TraceStep] = Field(default_factory=list)


class CaseView(BaseModel):
    case_id: str
    status: CaseStatus
    priority: Priority | None
    priority_overridden: bool
    reason: str
    english_summary: str | None
    location: Location
    people_count: int | None
    vulnerable: list[Vulnerability]
    water_level: WaterLevel
    medical_emergency: bool
    badges: list[Badge]
    assigned_team: str | None
    opened_at: datetime
    last_seen: datetime
    sources: list[SourceView]
    history: list[CaseEvent]


class ReplayStatus(BaseModel):
    running: bool
    split: str | None
    sent: int
    total: int
