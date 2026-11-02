"""Runs each message through the pipeline and keeps the dispatcher's view of every case.

Product promises enforced here:
- Residents are acknowledged honestly; "a team is on the way" is sent only after
  a dispatcher assigns one.
- Only a dispatcher closes a case (confirm safe).
- Every dispatcher decision is recorded with the dispatcher's name.
- A message the pipeline fails on is kept and acknowledged, never dropped.
"""

import logging
import threading
import time
import uuid
from datetime import UTC, datetime

from saklolo.agents.ask_back import apply_reply
from saklolo.agents.deps import PipelineDeps
from saklolo.agents.graph import run_pipeline
from saklolo.dispatch import replies
from saklolo.dispatch.case_view import build_case_view
from saklolo.dispatch.models import (
    CaseAction,
    CaseEvent,
    CaseStatus,
    CaseView,
    DispatchRecord,
    MessageRecord,
    ReceiveKind,
    ReceiveResult,
    rank,
)
from saklolo.dispatch.store import DispatchStore, InMemoryDispatchStore
from saklolo.domain.cases import Case
from saklolo.domain.errors import SakloloError
from saklolo.domain.models import (
    InboundMessage,
    OutboundMessage,
    Priority,
    TraceStatus,
    TraceStep,
    TriageOutcome,
)
from saklolo.domain.ports import Notifier

logger = logging.getLogger(__name__)

# A location reply is short ("Malanday po, tapat ng 7-Eleven"); anything longer
# may be a new update and goes through the whole pipeline instead.
MAX_LOCATION_REPLY_WORDS = 15


class CaseStateError(SakloloError):
    """The dispatcher action doesn't fit the case's current state."""


class DispatchService:
    def __init__(
        self, deps: PipelineDeps, notifier: Notifier, store: DispatchStore | None = None
    ) -> None:
        self._deps = deps
        self._notifier = notifier
        self._store = store or InMemoryDispatchStore()
        # Dedupe needs messages in order, and requests and replays share state.
        self._lock = threading.RLock()

    def receive(self, message: InboundMessage) -> ReceiveResult:
        with self._lock:
            record = self._as_location_reply(message) or self._triage(message)
            self._store.add_message(record)
            if record.case_id is not None and self._store.record(record.case_id) is None:
                self._store.save_record(record.case_id, DispatchRecord())
            return ReceiveResult(record=record, replies=self._reply(record))

    def cases(self, include_closed: bool = False) -> list[CaseView]:
        with self._lock:
            messages = self._store.messages()
            views = [self._view(case_id, messages) for case_id in self._store.case_ids()]
        visible = [v for v in views if include_closed or v.status != CaseStatus.CLOSED]
        return sorted(visible, key=lambda v: (rank(v.priority), v.opened_at))

    def case(self, case_id: str) -> CaseView:
        with self._lock:
            return self._view(case_id)

    def messages(self) -> list[MessageRecord]:
        with self._lock:
            return list(reversed(self._store.messages()))

    def assign(self, case_id: str, team: str, dispatcher: str) -> CaseView:
        with self._lock:
            case, record = self._case(case_id)
            if record.status == CaseStatus.CLOSED:
                raise CaseStateError(f"{case_id} is closed")
            record.status = CaseStatus.ASSIGNED
            record.assigned_team = team
            _log(record, CaseAction.ASSIGNED, dispatcher, team)
            self._store.save_record(case_id, record)
            for sender in sorted(case.senders):
                self._notifier.send_text(sender, replies.team_assigned(team))
            return self._view(case_id)

    def override(self, case_id: str, priority: Priority, reason: str, dispatcher: str) -> CaseView:
        with self._lock:
            _, record = self._case(case_id)
            record.override = priority
            record.override_reason = reason
            _log(record, CaseAction.OVERRIDDEN, dispatcher, f"{priority.value}: {reason}")
            self._store.save_record(case_id, record)
            return self._view(case_id)

    def confirm_safe(self, case_id: str, dispatcher: str) -> CaseView:
        with self._lock:
            case, record = self._case(case_id)
            case.closed = True
            self._deps.cases.save(case)
            record.status = CaseStatus.CLOSED
            _log(record, CaseAction.CLOSED, dispatcher, "Confirmed safe")
            self._store.save_record(case_id, record)
            return self._view(case_id)

    def _as_location_reply(self, message: InboundMessage) -> MessageRecord | None:
        """Resume a case waiting for its location, if this message answers the question."""
        if len(message.text.split()) > MAX_LOCATION_REPLY_WORDS:
            return None
        waiting = self._senders_case_awaiting_location(message)
        if waiting is None:
            return None
        started = time.perf_counter()
        location = apply_reply(waiting.case_id, message.text, self._deps.cases, self._deps.geocoder)
        if location.barangay is None:
            return None  # not a location after all: let the pipeline read it
        resumed = TraceStep(
            step="resume",
            status=TraceStatus.RAN,
            duration_ms=round((time.perf_counter() - started) * 1000),
            detail=(
                f"Resumed the paused case: {waiting.case_id} is in {location.barangay}. "
                "No model call."
            ),
        )
        return self._record(
            message, ReceiveKind.LOCATION_REPLY, case_id=waiting.case_id, trace=[resumed]
        )

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
        return self._record(
            message,
            ReceiveKind.TRIAGED,
            case_id=outcome.case_id,
            outcome=outcome,
            trace=state.trace,
        )

    def _record(
        self,
        message: InboundMessage,
        kind: ReceiveKind,
        case_id: str | None = None,
        outcome: TriageOutcome | None = None,
        error: str | None = None,
        trace: list[TraceStep] | None = None,
    ) -> MessageRecord:
        return MessageRecord(
            message_id=uuid.uuid4().hex[:12],
            message=message,
            kind=kind,
            outcome=outcome,
            case_id=case_id,
            error=error,
            trace=trace or [],
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
        record = self._store.record(case_id)
        if case is None or record is None:
            raise KeyError(case_id)
        return case, record

    def _view(self, case_id: str, messages: list[MessageRecord] | None = None) -> CaseView:
        case, record = self._case(case_id)
        all_messages = self._store.messages() if messages is None else messages
        sources = [r for r in all_messages if r.case_id == case_id]
        return build_case_view(case, record, sources)


def _log(record: DispatchRecord, action: CaseAction, dispatcher: str, detail: str) -> None:
    record.history.append(
        CaseEvent(action=action, dispatcher=dispatcher, at=datetime.now(UTC), detail=detail)
    )
