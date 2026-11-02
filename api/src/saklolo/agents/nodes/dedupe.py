"""Attach the message to an open case or open a new one (ADR 0003).

Messages that aren't about a household (questions, relief requests) get no case.
Nothing here closes a case: "rescued na" marks it reported safe for a dispatcher
to confirm, so a misread update can't make a household disappear.
"""

import logging

from saklolo.agents.deps import PipelineDeps
from saklolo.agents.state import PipelineState
from saklolo.domain.cases import Case, find_matching_case
from saklolo.domain.errors import ServiceUnavailableError
from saklolo.domain.models import ExtractedRequest, StatusUpdateKind

logger = logging.getLogger(__name__)


def dedupe(state: PipelineState, deps: PipelineDeps) -> None:
    extraction = state.extraction
    if extraction is None or not (extraction.is_rescue_request or extraction.is_status_update):
        return

    now = state.message.received_at
    embedding = _embed(dedupe_text(extraction), deps)
    match = find_matching_case(
        deps.cases.open_cases(since=now - deps.dedupe.window),
        state.message.sender,
        embedding,
        state.location,
        now,
        deps.dedupe,
    )
    if match:
        state.dedupe_similarity = match.similarity
        state.dedupe_same_sender = match.same_sender
    case = _merge(match.case, state) if match else _open(state, embedding, deps)
    if extraction.status_update_kind == StatusUpdateKind.RESCUED:
        case.reported_safe = True
    deps.cases.save(case)
    state.case_id = case.case_id
    _adopt_case_location(state, case)


def dedupe_text(extraction: ExtractedRequest) -> str:
    """English summary plus the place words: comparable across Taglish rewordings."""
    return f"{extraction.english_summary} | {extraction.location_text or ''}"


def _embed(text: str, deps: PipelineDeps) -> list[float]:
    try:
        return deps.embedder.embed(text)
    except ServiceUnavailableError:
        # Without embeddings only same-sender matching works; never fail the message.
        logger.warning("embedder unavailable; dedupe falls back to sender matching")
        return []


def _merge(case: Case, state: PipelineState) -> Case:
    case.senders.add(state.message.sender)
    case.last_seen = state.message.received_at
    case.message_count += 1
    if case.awaiting_location and state.location.barangay is not None:
        case.location = state.location
    return case


def _open(state: PipelineState, embedding: list[float], deps: PipelineDeps) -> Case:
    received = state.message.received_at
    return Case(
        case_id=deps.cases.next_id(),
        senders={state.message.sender},
        location=state.location,
        embedding=embedding,
        opened_at=received,
        last_seen=received,
    )


def _adopt_case_location(state: PipelineState, case: Case) -> None:
    """A later message may lack the place an earlier one gave; the case knows it."""
    if state.location.barangay is None and case.location.barangay is not None:
        state.location = case.location
        state.asks_location = False
