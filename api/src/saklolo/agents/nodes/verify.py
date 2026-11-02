"""Flag recycled posts: old pleas shared again in a new storm. No model call.

Two signals, either one flags the message:
- it copies a known past-typhoon post (the PostArchive), or
- it states a date in an earlier year ("Nov 12 2020", "Ondoy 2009").

A storm name alone is not a signal: residents say "parang Ulysses na naman" about a
real emergency. A flag never hides the message or lowers its priority; the dispatcher
sees the case with the reason and decides.
"""

import re

from saklolo.agents.deps import PipelineDeps
from saklolo.agents.state import PipelineState
from saklolo.domain.models import SuspicionReason

FIRST_YEAR = 1990
YEAR = re.compile(r"(?<![\d/.-])(19\d{2}|20\d{2})(?![\d/.-]?\d)")
DATE_YEAR = re.compile(r"\b\d{1,2}[/.-]\d{1,2}[/.-]((?:19|20)\d{2})\b")


def verify(state: PipelineState, deps: PipelineDeps) -> None:
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
    if SuspicionReason.RECYCLED not in state.suspicion_reasons:
        state.suspicion_reasons.append(SuspicionReason.RECYCLED)


def past_year(text: str, current_year: int) -> int | None:
    """The most recent earlier year the text states, if any."""
    years = [int(y) for y in YEAR.findall(text)] + [int(y) for y in DATE_YEAR.findall(text)]
    past = [year for year in years if FIRST_YEAR <= year < current_year]
    return max(past, default=None)
