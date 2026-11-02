import pytest
from pydantic import ValidationError

from saklolo.domain.models import Priority, TriageDecision


def test_low_confidence_triage_needs_escalation() -> None:
    decision = TriageDecision(priority=Priority.CRITICAL, reason="Water at roof", confidence=0.6)

    assert decision.needs_escalation(threshold=0.75)


def test_confident_triage_stays_on_fast_path() -> None:
    decision = TriageDecision(
        priority=Priority.HIGH, reason="Trapped, water steady", confidence=0.9
    )

    assert not decision.needs_escalation(threshold=0.75)


def test_confidence_outside_unit_range_is_rejected() -> None:
    with pytest.raises(ValidationError):
        TriageDecision(priority=Priority.INFO, reason="Relief request", confidence=1.5)
