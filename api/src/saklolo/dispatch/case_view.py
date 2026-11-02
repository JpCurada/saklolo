"""Combine a case, the dispatcher's decisions, and its messages into one queue row."""

from collections.abc import Iterable

from saklolo.dispatch.models import (
    Badge,
    CaseStatus,
    CaseView,
    DispatchRecord,
    MessageRecord,
    SourceView,
    rank,
)
from saklolo.domain.cases import Case
from saklolo.domain.models import Priority, TriageOutcome, WaterLevel


def build_case_view(case: Case, record: DispatchRecord, sources: list[MessageRecord]) -> CaseView:
    outcomes = [s.outcome for s in sources if s.outcome is not None]
    top = _most_urgent(outcomes)
    latest = outcomes[-1] if outcomes else None
    return CaseView(
        case_id=case.case_id,
        status=CaseStatus.CLOSED if case.closed else record.status,
        priority=record.override or (top.priority if top else None),
        priority_overridden=record.override is not None,
        reason=record.override_reason or (top.reason if top else ""),
        # The row must explain its priority; later updates show up as badges and sources.
        english_summary=(top.english_summary if top else None)
        or _latest(o.english_summary for o in outcomes),
        location=case.location,
        people_count=_latest(o.people_count for o in outcomes),
        vulnerable=sorted({v for o in outcomes for v in o.vulnerable}),
        water_level=latest.water_level if latest else WaterLevel.UNKNOWN,
        medical_emergency=any(o.medical_emergency for o in outcomes),
        badges=_badges(case, record, outcomes),
        assigned_team=record.assigned_team,
        opened_at=case.opened_at,
        last_seen=case.last_seen,
        sources=[_source(s) for s in sources],
    )


def _most_urgent(outcomes: list[TriageOutcome]) -> TriageOutcome | None:
    """The most urgent message wins; among equals, the latest one explains why."""
    with_priority = [o for o in outcomes if o.priority is not None]
    if not with_priority:
        return None
    best = min(rank(o.priority) for o in with_priority)
    return [o for o in with_priority if rank(o.priority) == best][-1]


def _latest[T](values: Iterable[T | None]) -> T | None:
    present = [v for v in values if v is not None]
    return present[-1] if present else None


def _badges(case: Case, record: DispatchRecord, outcomes: list[TriageOutcome]) -> list[Badge]:
    checks = {
        Badge.CORROBORATED: len(case.senders) >= 2,
        Badge.SUSPICIOUS: any(o.is_suspicious for o in outcomes),
        Badge.REPORTED_SAFE: case.reported_safe and not case.closed,
        Badge.AWAITING_LOCATION: case.awaiting_location and not case.closed,
        Badge.NEEDS_REVIEW: any(o.needs_escalation for o in outcomes),
        Badge.OVERRIDDEN: record.override is not None,
    }
    return [badge for badge, applies in checks.items() if applies]


def _source(record: MessageRecord) -> SourceView:
    outcome = record.outcome
    priority: Priority | None = outcome.priority if outcome else None
    return SourceView(
        message_id=record.message_id,
        sender=record.message.sender,
        channel=record.message.channel,
        received_at=record.message.received_at,
        text=record.message.text,
        english_summary=outcome.english_summary if outcome else None,
        priority=priority,
    )
