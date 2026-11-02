"""What each Graph step did to one message, in words a dispatcher can check.

The trace is recorded as the graph runs, from the same state the steps write, so the
timeline in the dashboard is never a reconstruction.
"""

from saklolo.agents.deps import PipelineDeps
from saklolo.agents.state import PipelineState, PrefilterVerdict
from saklolo.domain.models import LocationSource, TraceStatus, TraceStep

# Graph order, so skipped steps can be listed where they would have run.
STEP_ORDER = [
    "normalize",
    "prefilter",
    "extract",
    "geolocate",
    "dedupe",
    "verify",
    "triage",
    "escalate",
]


def record(
    step: str,
    state: PipelineState,
    deps: PipelineDeps,
    duration_ms: int,
    model_calls_before: int,
) -> None:
    """Append what `step` just did. Call right after the step ran."""
    called_model = len(state.usage) > model_calls_before
    detail, service = _DESCRIBE[step](state, deps)
    if called_model:
        model_id = deps.escalation_model_id if step == "escalate" else deps.model_id
        service = f"Bedrock · {model_id}" if model_id else "Bedrock"
        if step == "escalate":
            service = f"Strands Swarm · {service}"
    state.trace.append(
        TraceStep(
            step=step,
            status=TraceStatus.RAN,
            duration_ms=duration_ms,
            service=service,
            detail=detail,
        )
    )


def with_skipped(state: PipelineState) -> list[TraceStep]:
    """The trace in graph order, with the steps that didn't run and why."""
    ran = {step.step: step for step in state.trace}
    return [
        ran.get(step)
        or TraceStep(
            step=step, status=TraceStatus.SKIPPED, duration_ms=0, detail=_skip_reason(step, state)
        )
        for step in STEP_ORDER
    ]


def _skip_reason(step: str, state: PipelineState) -> str:
    if state.verdict == PrefilterVerdict.SPAM:
        return "Skipped: spam stops before any model call"
    if step == "escalate" and state.decision is not None:
        return "Not needed: triage was confident"
    return "Skipped"


Described = tuple[str, str | None]


def _normalize(state: PipelineState, _: PipelineDeps) -> Described:
    masked = len(state.phones)
    return (
        f"Cleaned the text; masked {masked} phone number(s)" if masked else "Cleaned the text"
    ), None


def _prefilter(state: PipelineState, _: PipelineDeps) -> Described:
    if state.verdict == PrefilterVerdict.SPAM:
        return f"Flagged, not deleted: {state.verdict_reason.lower()}", None
    if state.injection_suspected:
        return "Needs a model; flagged: it contains instructions aimed at the system", None
    return "Needs a model", None


def _extract(state: PipelineState, _: PipelineDeps) -> Described:
    request = state.extraction
    if request is None:
        return "Nothing extracted", None
    if not (request.is_rescue_request or request.is_status_update):
        return "Not a rescue request", None
    people = f"{request.people_count} people" if request.people_count else "People unknown"
    vulnerable = ", ".join(request.vulnerable) or "no one vulnerable mentioned"
    return f"{people}; {vulnerable}; water: {request.water_level}", None


def _geolocate(state: PipelineState, _: PipelineDeps) -> Described:
    location = state.location
    if location.barangay is None:
        if state.asks_location:
            return "No barangay found: will ask the resident where they are", None
        return "No location needed", None
    if location.source == LocationSource.GEOCODER:
        return f"{location.barangay}, found from the place words", "Amazon Location"
    return f"{location.barangay}, named in the message", None


def _dedupe(state: PipelineState, _: PipelineDeps) -> Described:
    if state.case_id is None:
        return "No case: not about a household", None
    if state.dedupe_similarity is None:
        return f"Opened {state.case_id}", "Titan embeddings"
    if state.dedupe_same_sender:
        return f"Same sender: added to {state.case_id}", "Titan embeddings"
    return (
        f"Merged into {state.case_id}: {state.dedupe_similarity:.2f} similar and nearby",
        "Titan embeddings",
    )


def _verify(state: PipelineState, _: PipelineDeps) -> Described:
    notes = []
    if state.recycled_note:
        notes.append(f"Possible old post: {state.recycled_note}")
    if state.sender_note:
        notes.append(f"Unusual sender: {state.sender_note}")
    verdict = f"{'; '.join(notes)}. Flagged, still shown" if notes else "No sign of an old post"
    return (f"{verdict} · {state.flood_note}" if state.flood_note else verdict), None


def _triage(state: PipelineState, deps: PipelineDeps) -> Described:
    decision = state.decision
    if decision is None:
        return state.verdict_reason or "No priority", None
    review = (
        "below the review threshold: a human decides"
        if decision.needs_escalation(deps.escalation_threshold)
        else "confident"
    )
    return (
        f"{decision.priority.value}: {decision.reason} ({decision.confidence:.2f}, {review})",
        None,
    )


def _escalate(state: PipelineState, _: PipelineDeps) -> Described:
    parts = [state.escalation_note]
    if state.escalation_agents:
        parts.append(" → ".join(state.escalation_agents))
    if state.escalation_lookups:
        parts.append("Looked up " + "; ".join(state.escalation_lookups))
    return " · ".join(parts), None


_DESCRIBE = {
    "normalize": _normalize,
    "prefilter": _prefilter,
    "extract": _extract,
    "geolocate": _geolocate,
    "dedupe": _dedupe,
    "verify": _verify,
    "triage": _triage,
    "escalate": _escalate,
}
