from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from saklolo.adapters.corrections import InMemoryCorrectionMemory
from saklolo.adapters.outbox import InMemoryOutbox
from saklolo.dispatch import replies
from saklolo.dispatch.models import Badge, CaseAction, CaseStatus, ReceiveKind
from saklolo.dispatch.service import CaseStateError, DispatchService
from saklolo.domain.errors import ServiceUnavailableError
from saklolo.domain.models import (
    Channel,
    ExtractedRequest,
    InboundMessage,
    Priority,
    TriageDecision,
    WaterLevel,
)
from saklolo.domain.ports import PastCorrection
from tests.agents.fakes import FakeStructuredModel, fake_deps

T0 = datetime(2026, 11, 10, 9, tzinfo=UTC)
NENA, MARK = "+639000000001", "+639000000002"


def extraction_for(prompt: str) -> ExtractedRequest:
    """Reads the message like a model would, for the handful of texts used here."""
    text = prompt.lower()
    vague = "7-11" in text
    return ExtractedRequest(
        is_rescue_request="bubong" in text or "tuhod" in text or "tubig" in text,
        is_status_update=False,
        people_count=5,
        water_level=WaterLevel.ROOF if "bubong" in text else WaterLevel.KNEE,
        location_text="tapat ng 7-11" if vague else "likod ng kapilya",
        barangay=None if vague else ("Fortune" if "fortune" in text else "Malanday"),
        english_summary="5 people on the roof" if "bubong" in text else "Family, knee-deep",
        confidence=0.9,
    )


def decision_for(prompt: str) -> TriageDecision:
    critical = "roof" in prompt.lower()
    return TriageDecision(
        priority=Priority.CRITICAL if critical else Priority.HIGH,
        reason="On the roof" if critical else "Trapped, water low",
        confidence=0.9,
    )


def make_service(
    model: FakeStructuredModel | None = None,
) -> tuple[DispatchService, InMemoryOutbox]:
    model = model or FakeStructuredModel(
        {ExtractedRequest: extraction_for, TriageDecision: decision_for}
    )
    outbox = InMemoryOutbox()
    return DispatchService(fake_deps(model), outbox), outbox


def message(text: str, sender: str = NENA, minutes: int = 0) -> InboundMessage:
    return InboundMessage(
        sender=sender, text=text, channel=Channel.SMS, received_at=T0 + timedelta(minutes=minutes)
    )


def test_rescue_request_is_queued_and_acknowledged_honestly() -> None:
    service, outbox = make_service()

    result = service.receive(message("tulong nasa bubong kami"))

    [case] = service.cases()
    assert case.priority == Priority.CRITICAL
    assert case.reason == "On the roof"
    assert [s.text for s in case.sources] == ["tulong nasa bubong kami"]
    assert [r.body for r in result.replies] == [replies.ACKNOWLEDGED]
    assert all("papunta" not in m.body for m in outbox.sent())  # no promise before a team


def test_queue_puts_the_most_urgent_case_first() -> None:
    service, _ = make_service()
    service.receive(message("tubig hanggang tuhod sa fortune", sender=MARK))
    service.receive(message("nasa bubong kami", minutes=5))

    assert [c.priority for c in service.cases()] == [Priority.CRITICAL, Priority.HIGH]


def test_assigning_a_team_tells_every_sender_on_the_case() -> None:
    service, outbox = make_service()
    service.receive(message("nasa bubong kami"))
    service.receive(message("pamilya ko nasa bubong", sender=MARK, minutes=10))
    [case] = service.cases()

    assigned = service.assign(case.case_id, "Team Bravo", "Ana")

    assert assigned.status == CaseStatus.ASSIGNED
    assert Badge.CORROBORATED in assigned.badges
    told = {m.recipient for m in outbox.sent() if m.body == replies.team_assigned("Team Bravo")}
    assert told == {NENA, MARK}


def test_only_a_dispatcher_closes_a_case() -> None:
    service, _ = make_service()
    service.receive(message("nasa bubong kami"))
    [case] = service.cases()

    service.confirm_safe(case.case_id, "Ana")

    assert service.cases() == []
    assert service.cases(include_closed=True)[0].status == CaseStatus.CLOSED
    with pytest.raises(CaseStateError):
        service.assign(case.case_id, "Team Bravo", "Ana")


def test_override_sets_priority_and_badge() -> None:
    service, _ = make_service()
    service.receive(message("nasa bubong kami"))
    [case] = service.cases()

    overridden = service.override(case.case_id, Priority.HIGH, "Already on a safe roof deck", "Ana")

    assert overridden.priority == Priority.HIGH
    assert overridden.reason == "Already on a safe roof deck"
    assert Badge.OVERRIDDEN in overridden.badges


def test_location_reply_resumes_the_case_without_a_model_call() -> None:
    service, outbox = make_service()
    first = service.receive(message("nasa bubong kami tapat ng 7-11"))
    calls_before = len(service._deps.model.calls)  # type: ignore[attr-defined]

    reply = service.receive(message("Malanday po", minutes=3))

    [case] = service.cases()
    assert first.replies[-1].body.startswith("Salamat po. Anong barangay")
    assert reply.record.kind == ReceiveKind.LOCATION_REPLY
    assert case.location.barangay == "Malanday"
    assert Badge.AWAITING_LOCATION not in case.badges
    assert len(service._deps.model.calls) == calls_before  # type: ignore[attr-defined]
    assert outbox.sent(NENA)[-1].body == replies.LOCATION_RECEIVED
    [resumed] = reply.record.trace
    assert resumed.step == "resume"
    assert resumed.detail.startswith(f"Resumed the paused case: {case.case_id} is in Malanday")
    assert first.record.trace[0].step == "normalize"


def test_an_update_from_a_sender_awaiting_location_is_not_mistaken_for_a_reply() -> None:
    service, _ = make_service()
    service.receive(message("nasa bubong kami tapat ng 7-11"))

    update = service.receive(message("tumataas na ang tubig, hindi na kami makababa", minutes=3))

    assert update.record.kind == ReceiveKind.TRIAGED


def test_pipeline_failure_keeps_and_acknowledges_the_message() -> None:
    def broken(_: str) -> ExtractedRequest:
        raise RuntimeError("model down")

    service, _ = make_service(FakeStructuredModel({ExtractedRequest: broken}))

    result = service.receive(message("nasa bubong kami"))

    assert result.record.error == "RuntimeError"
    assert service.messages()[0].message.text == "nasa bubong kami"
    assert [r.body for r in result.replies] == [replies.ACKNOWLEDGED]


def test_spam_gets_no_reply_and_no_case() -> None:
    service, outbox = make_service()

    result = service.receive(message("LEGIT LOAN APPROVAL 5 MINS"))

    assert result.replies == []
    assert outbox.sent() == []
    assert service.cases() == []


def test_summary_explains_the_most_urgent_message_not_the_latest() -> None:
    service, _ = make_service()
    service.receive(message("nasa bubong kami"))
    service.receive(message("tubig hanggang tuhod na lang", minutes=30))

    [case] = service.cases()

    assert case.priority == Priority.CRITICAL
    assert case.english_summary == "5 people on the roof"


def test_every_decision_is_recorded_with_who_made_it() -> None:
    service, _ = make_service()
    service.receive(message("nasa bubong kami"))
    [case] = service.cases()

    service.override(case.case_id, Priority.HIGH, "Safe roof deck", "Ana")
    service.assign(case.case_id, "Team Bravo", "Ben")
    closed = service.confirm_safe(case.case_id, "Ana")

    assert [(e.action, e.dispatcher, e.detail) for e in closed.history] == [
        (CaseAction.OVERRIDDEN, "Ana", "P2: Safe roof deck"),
        (CaseAction.ASSIGNED, "Ben", "Team Bravo"),
        (CaseAction.CLOSED, "Ana", "Confirmed safe"),
    ]


def test_an_override_is_remembered_without_phone_numbers() -> None:
    memory = InMemoryCorrectionMemory()
    service = DispatchService(
        replace(
            fake_deps(
                FakeStructuredModel(
                    {ExtractedRequest: extraction_for, TriageDecision: decision_for}
                )
            ),
            corrections=memory,
        ),
        InMemoryOutbox(),
    )
    service.receive(message("nasa bubong kami"))
    [case] = service.cases()

    service.override(case.case_id, Priority.HIGH, "Called 09170000000, safe deck", "Ana")

    [remembered] = memory.similar("5 people on the roof")
    assert (remembered.first_priority, remembered.corrected_priority) == (
        Priority.CRITICAL,
        Priority.HIGH,
    )
    assert "09170000000" not in remembered.reason


def test_a_memory_failure_never_blocks_the_dispatcher() -> None:
    class Down(InMemoryCorrectionMemory):
        def remember(self, correction: PastCorrection) -> None:
            raise ServiceUnavailableError("down")

    service = DispatchService(
        replace(
            fake_deps(
                FakeStructuredModel(
                    {ExtractedRequest: extraction_for, TriageDecision: decision_for}
                )
            ),
            corrections=Down(),
        ),
        InMemoryOutbox(),
    )
    service.receive(message("nasa bubong kami"))
    [case] = service.cases()

    updated = service.override(case.case_id, Priority.HIGH, "Safe deck", "Ana")

    assert updated.priority == Priority.HIGH
