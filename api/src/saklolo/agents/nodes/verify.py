"""Flag recycled posts and unusual senders. No model call.

A recycled post is an old plea shared again in a new storm. Two signals, either one
flags the message:
- it copies a known past-typhoon post (the PostArchive), or
- it states a date in an earlier year ("Nov 12 2020", "Ondoy 2009").

One sender reporting several barangays in the dedupe window is flagged too. It may be
a hoax, and it may be a barangay volunteer, so the dispatcher decides.

A storm name alone is not a signal: residents say "parang Ulysses na naman" about a
real emergency. A flag never hides the message or lowers its priority; the dispatcher
sees the case with the reason and decides.
"""

import re

from saklolo.agents.deps import PipelineDeps
from saklolo.agents.state import PipelineState
from saklolo.domain.models import SuspicionReason

FIRST_YEAR = 1990
MANY_BARANGAYS = 3
YEAR = re.compile(r"(?<![\d/.-])(19\d{2}|20\d{2})(?![\d/.-]?\d)")
DATE_YEAR = re.compile(r"\b\d{1,2}[/.-]\d{1,2}[/.-]((?:19|20)\d{2})\b")


def verify(state: PipelineState, deps: PipelineDeps) -> None:
    _check_old_post(state, deps)
    _check_sender(state, deps)


def _check_sender(state: PipelineState, deps: PipelineDeps) -> None:
    since = state.message.received_at - deps.dedupe.window
    places = {
        case.location.barangay
        for case in deps.cases.open_cases(since=since)
        if state.message.sender in case.senders and case.location.barangay is not None
    }
    if len(places) >= MANY_BARANGAYS:
        state.sender_note = f"Same sender reported {len(places)} barangays"
        _flag(state, SuspicionReason.SENDER_PATTERN)


def _check_old_post(state: PipelineState, deps: PipelineDeps) -> None:
    text = state.model_text
    match = deps.archive.match(text) if deps.archive else None
    if match is not None:
        state.recycled_note = (
            f"Copies a {match.posted.year} post ({match.archive_id}, "
            f"{match.similarity:.2f} similar)"
        )
    elif year := past_year(text, state.message.received_at.year):
        state.recycled_note = f"Mentions a date in {year}"
    else:
        return
    _flag(state, SuspicionReason.RECYCLED)


def _flag(state: PipelineState, reason: SuspicionReason) -> None:
    if reason not in state.suspicion_reasons:
        state.suspicion_reasons.append(reason)


def past_year(text: str, current_year: int) -> int | None:
    """The most recent earlier year the text states, if any."""
    years = [int(y) for y in YEAR.findall(text)] + [int(y) for y in DATE_YEAR.findall(text)]
    past = [year for year in years if FIRST_YEAR <= year < current_year]
    return max(past, default=None)
