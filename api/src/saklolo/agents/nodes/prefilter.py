"""Catch obvious spam with rules, so it never costs a model call.

Conservative by design: a rescue request mislabeled here would skip triage, so
anything with a distress word goes to the model, and nothing here closes a case.
Prompt-injection phrases are flagged for the dispatcher but still go to the model;
the text only ever reaches it inside <message> tags.
"""

import re

from saklolo.agents.state import PipelineState, PrefilterVerdict


def _any(*patterns: str) -> re.Pattern[str]:
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)


DISTRESS = _any(
    r"\btulong\b",
    r"\btulungan\b",
    r"\bsaklolo\b",
    r"\bhelp",
    r"\bsos\b",
    r"\bemergency\b",
    r"\brescue\b",
    r"\btrapped\b",
    r"\bstranded\b",
    r"\bnaiipit\b",
    r"\bnaiwan\b",
    r"\blubog\b",
    r"\blumulubog\b",
    r"\bnalulunod\b",
    r"\bbubong\b",
    r"\bleeg\b",
    r"\bdibdib\b",
    r"\bbewang\b",
    r"\bbaha\b",
    r"\btubig\b",
    r"\bbuntis\b",
    r"\bbaby\b",
    r"\bbangka\b",
)
SPAM = _any(
    r"\bloan\b",
    r"\bgcash\b",
    r"forward (this|to)",
    r"\bnanalo\b",
    r"\bpromo\b",
    r"\bclick\b",
    r"\blink\b",
)
PROMPT_INJECTION = _any(
    r"ignore (all |the )?(previous|above|prior) instructions",
    r"system prompt",
    r"you are now",
)
# The whole message must be a greeting or test; "Good morning po, stranded kami" is not.
NO_CONTENT = _any(r"^\W*(test|testing|hello|hi|gm|good morning)(\W+po)?\W*$")


def prefilter(state: PipelineState) -> None:
    text = state.clean_text
    state.injection_suspected = bool(PROMPT_INJECTION.search(text))
    if DISTRESS.search(text):
        _set(state, PrefilterVerdict.NEEDS_MODEL, "")
    elif state.injection_suspected:
        _set(state, PrefilterVerdict.NEEDS_MODEL, "Contains instructions aimed at the system")
    elif SPAM.search(text) or NO_CONTENT.search(text):
        _set(state, PrefilterVerdict.SPAM, "Matches a spam or no-content pattern")
    else:
        _set(state, PrefilterVerdict.NEEDS_MODEL, "")


def needs_model(state: PipelineState) -> bool:
    return state.verdict == PrefilterVerdict.NEEDS_MODEL


def _set(state: PipelineState, verdict: PrefilterVerdict, reason: str) -> None:
    state.verdict = verdict
    state.verdict_reason = reason
