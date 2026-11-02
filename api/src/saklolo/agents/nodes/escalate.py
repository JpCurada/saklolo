"""Low-confidence triage gets a second opinion from a Swarm (ADR 0002).

A barangay the reviewers found with the geocoder replaces an unknown location: it is
the geocoder's answer, not the model's words. The ask-back still goes out, so the
resident can correct a landmark match.

The Swarm may confirm or raise a priority. It never lowers one on its own: a lower
suggestion keeps the original priority and leaves the case to a human, because a
missed critical case is the worst mistake the system can make.
"""

import logging

from saklolo.agents.deps import PipelineDeps
from saklolo.agents.nodes.extract import message_block
from saklolo.agents.state import EscalationOutcome, PipelineState
from saklolo.domain.models import LocationSource, TriageDecision
from saklolo.domain.ports import PlaceLookup

logger = logging.getLogger(__name__)


def needs_escalation(state: PipelineState, threshold: float) -> bool:
    return state.decision is not None and state.decision.needs_escalation(threshold)


def escalate(state: PipelineState, deps: PipelineDeps) -> None:
    current = state.decision
    if current is None:
        return
    state.first_decision = current
    if deps.escalation is None:
        state.escalation_outcome = EscalationOutcome.NOT_CONFIGURED
        state.escalation_note = "No reviewers configured: a human decides"
        return
    try:
        review = deps.escalation.review(brief(state, current))
    except Exception as error:  # a reviewer outage must never lose the message
        logger.warning("escalation failed: %s", type(error).__name__)
        state.escalation_outcome = EscalationOutcome.UNAVAILABLE
        state.escalation_note = "Reviewers unavailable: a human decides"
        return

    state.usage.append(review.usage)
    state.escalation_agents = list(review.agents)
    state.escalation_lookups = [_describe(lookup) for lookup in review.lookups]
    _adopt_found_location(state, review.lookups, deps)
    proposed = review.decision
    if proposed is None:
        state.escalation_outcome = EscalationOutcome.UNDECIDED
        state.escalation_note = "Reviewers couldn't agree: a human decides"
    elif _less_urgent(proposed, current):
        state.escalation_outcome = EscalationOutcome.REFUSED
        state.escalation_note = (
            f"Reviewers suggested {proposed.priority.value}; kept {current.priority.value} "
            "for a human to decide"
        )
    else:
        state.escalation_outcome = (
            EscalationOutcome.CONFIRMED
            if proposed.priority == current.priority
            else EscalationOutcome.RAISED
        )
        state.decision = proposed
        verdict = (
            "still unsure: a human decides"
            if proposed.needs_escalation(deps.escalation_threshold)
            else "confirmed by reviewers"
        )
        state.escalation_note = (
            f"{proposed.priority.value}: {proposed.reason} ({proposed.confidence:.2f}, {verdict})"
        )


def brief(state: PipelineState, decision: TriageDecision) -> str:
    """Everything the reviewers need. The resident's words stay inside <message> tags."""
    extraction = state.extraction
    facts = extraction.model_dump_json(exclude={"confidence"}) if extraction else "{}"
    place = state.location.barangay or "unknown"
    merged = (
        f"merged into {state.case_id} ({state.dedupe_similarity:.2f} similar)"
        if state.dedupe_similarity is not None
        else f"case {state.case_id or 'none'}"
    )
    return (
        f"{message_block(state.model_text)}\n"
        f"<facts>\n{facts}\nbarangay: {place}\ncase: {merged}\n"
        f"old post check: {state.recycled_note or 'no sign of an old post'}\n"
        f"sender check: {state.sender_note or 'nothing unusual'}\n</facts>\n"
        f"<first_triage>\n{decision.model_dump_json()}\n</first_triage>"
    )


def _less_urgent(proposed: TriageDecision, current: TriageDecision) -> bool:
    # "P1" sorts before "P2": a larger value is less urgent.
    return proposed.priority.value > current.priority.value


def _describe(lookup: PlaceLookup) -> str:
    if lookup.unavailable:
        answer = "lookup unavailable"
    elif lookup.location is None:
        answer = "not found"
    else:
        answer = lookup.location.barangay or "not found"
    return f'"{lookup.query}" → {answer}'


def _adopt_found_location(
    state: PipelineState, lookups: tuple[PlaceLookup, ...], deps: PipelineDeps
) -> None:
    """Use the last barangay the geocoder found, if the case has none yet."""
    found = [lookup.location for lookup in lookups if lookup.location and lookup.location.barangay]
    if not found or state.location.barangay is not None:
        return
    state.location = found[-1].model_copy(update={"source": LocationSource.GEOCODER})
    case = deps.cases.get(state.case_id) if state.case_id else None
    if case is not None and case.location.barangay is None:
        case.location = state.location
        deps.cases.save(case)
