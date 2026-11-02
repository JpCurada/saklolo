"""Runs each message through the pipeline and keeps the dispatcher's view of every case.

Product promises enforced here:
- Residents are acknowledged honestly; "a team is on the way" is sent only after
  a dispatcher assigns one.
- Only a dispatcher closes a case (confirm safe).
- A message the pipeline fails on is kept and acknowledged, never dropped.
"""

import logging
import threading
import uuid

from saklolo.agents.ask_back import apply_reply
from saklolo.agents.deps import PipelineDeps
from saklolo.agents.graph import run_pipeline
from saklolo.dispatch import replies
from saklolo.dispatch.case_view import build_case_view
from saklolo.dispatch.models import (
    CaseStatus,
    CaseView,
    DispatchRecord,
    MessageRecord,
    ReceiveKind,
    ReceiveResult,
    rank,
)
from saklolo.domain.cases import Case
from saklolo.domain.errors import SakloloError
from saklolo.domain.models import InboundMessage, OutboundMessage, Priority, TriageOutcome
from saklolo.domain.ports import Notifier

logger = logging.getLogger(__name__)

# A location reply is short ("Malanday po, tapat ng 7-Eleven"); anything longer
# may be a new update and goes through the whole pipeline instead.
MAX_LOCATION_REPLY_WORDS = 15


class CaseStateError(SakloloError):
    """The dispatcher action doesn't fit the case's current state."""


class DispatchService:
    def __init__(self, deps: PipelineDeps, notifier: Notifier) -> None:
        self._deps = deps
        self._notifier = notifier
        self._records: list[MessageRecord] = []
        self._dispatch: dict[str, DispatchRecord] = {}
        # Dedupe needs messages in order, and requests and replays share state.
        self._lock = threading.RLock()

    def receive(self, message: InboundMessage) -> ReceiveResult:
        with self._lock:
            record = self._as_location_reply(message) or self._triage(message)
            self._records.append(record)
            if record.case_id is not None:
                self._dispatch.setdefault(record.case_id, DispatchRecord())
            return ReceiveResult(record=record, replies=self._reply(record))

    def cases(self, include_closed: bool = False) -> list[CaseView]:
        with self._lock:
            views = [self._view(case_id) for case_id in self._dispatch]
        visible = [v for v in views if include_closed or v.status != CaseStatus.CLOSED]
        return sorted(visible, key=lambda v: (rank(v.priority), v.opened_at))

    def case(self, case_id: str) -> CaseView:
        with self._lock:
            return self._view(case_id)

    def messages(self) -> list[MessageRecord]:
        with self._lock:
            return list(reversed(self._records))

    def assign(self, case_id: str, team: str) -> CaseView:
        with self._lock:
            case, record = self._case(case_id)
            if record.status == CaseStatus.CLOSED:
                raise CaseStateError(f"{case_id} is closed")
            record.status = CaseStatus.ASSIGNED
            record.assigned_team = team
            for sender in sorted(case.senders):
                self._notifier.send_text(sender, replies.team_assigned(team))
            return self._view(case_id)

    def override(self, case_id: str, priority: Priority, reason: str) -> CaseView:
        with self._lock:
            _, record = self._case(case_id)
            record.override = priority
            record.override_reason = reason
            return self._view(case_id)

    def confirm_safe(self, case_id: str) -> CaseView:
        with self._lock:
            case, record = self._case(case_id)
            case.closed = True
            self._deps.cases.save(case)
            record.status = CaseStatus.CLOSED
            return self._view(case_id)

    def _as_location_reply(self, message: InboundMessage) -> MessageRecord | None:
        """Resume a case waiting for its location, if this message answers the question."""
        if len(message.text.split()) > MAX_LOCATION_REPLY_WORDS:
            return None
        waiting = self._senders_case_awaiting_location(message)
        if waiting is None:
            return None
        location = apply_reply(waiting.case_id, message.text, self._deps.cases, self._deps.geocoder)
        if location.barangay is None:
            return None  # not a location after all: let the pipeline read it
        return self._record(message, ReceiveKind.LOCATION_REPLY, case_id=waiting.case_id)

    def _senders_case_awaiting_location(self, message: InboundMessage) -> Case | None:
        since = message.received_at - self._deps.dedupe.window
        own = [
            c
            for c in self._deps.cases.open_cases(since=since)
            if message.sender in c.senders and c.awaiting_location
        ]
        return max(own, key=lambda c: c.last_seen, default=None)

    def _triage(self, message: InboundMessage) -> MessageRecord:
        try:
            state = run_pipeline(message, self._deps)
        except Exception as error:  # keep the message for a human; never drop it
            logger.exception("pipeline failed; message kept for review")
            return self._record(message, ReceiveKind.TRIAGED, error=f"{type(error).__name__}")
        outcome = state.outcome(self._deps.escalation_threshold)
        return self._record(message, ReceiveKind.TRIAGED, case_id=outcome.case_id, outcome=outcome)

    def _record(
        self,
        message: InboundMessage,
        kind: ReceiveKind,
        case_id: str | None = None,
        outcome: TriageOutcome | None = None,
        error: str | None = None,
    ) -> MessageRecord:
        return MessageRecord(
            message_id=uuid.uuid4().hex[:12],
            message=message,
            kind=kind,
            outcome=outcome,
            case_id=case_id,
            error=error,
        )

    def _reply(self, record: MessageRecord) -> list[OutboundMessage]:
        bodies = self._reply_bodies(record)
        sender = record.message.sender
        for body in bodies:
            self._notifier.send_text(sender, body)
        return [
            OutboundMessage(recipient=sender, body=body, sent_at=record.message.received_at)
            for body in bodies
        ]

    @staticmethod
    def _reply_bodies(record: MessageRecord) -> list[str]:
        if record.kind == ReceiveKind.LOCATION_REPLY:
            return [replies.LOCATION_RECEIVED]
        outcome = record.outcome
        if outcome is not None and outcome.is_suspicious and outcome.case_id is None:
            return []  # don't confirm a live number to spammers
        bodies = [replies.ACKNOWLEDGED]
        if outcome is not None and outcome.ask_back_question:
            bodies.append(outcome.ask_back_question)
        return bodies

    def _case(self, case_id: str) -> tuple[Case, DispatchRecord]:
        case = self._deps.cases.get(case_id)
        record = self._dispatch.get(case_id)
        if case is None or record is None:
            raise KeyError(case_id)
        return case, record

    def _view(self, case_id: str) -> CaseView:
        case, record = self._case(case_id)
        sources = [r for r in self._records if r.case_id == case_id]
        return build_case_view(case, record, sources)
