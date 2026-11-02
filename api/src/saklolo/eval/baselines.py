"""Trivial predictors that set the bar the agents must beat."""

import time
from collections.abc import Sequence

from saklolo.domain.models import Priority
from saklolo.domain.places import BARANGAY_SPELLINGS, fold
from saklolo.eval.types import EvalMessage, Prediction

SPAM_WORDS = ("loan", "gcash", "forward this", "nanalo", "promo", "ignore previous")
CLOSED_WORDS = ("rescued", "nasundo", "nakalikas", "na rescue", "na-rescue")
SUSPICIOUS_WORDS = ("2020", "#ulyssesph", "repost", "[screenshot]")
PRIORITY_WORDS: tuple[tuple[Priority, tuple[str, ...]], ...] = (
    (Priority.CRITICAL, ("bubong", "roof", "leeg", "neck", "lampas tao", "dibdib", "dumudugo")),
    (Priority.HIGH, ("trapped", "2nd floor", "2nd flr", "second floor", "palapag", "taas")),
    (Priority.MODERATE, ("lumikas", "evac", "sundo", "sunduin")),
)


class KeywordBaseline:
    """Keyword rules, one case per sender, no model calls."""

    name = "keyword"

    def predict(self, messages: Sequence[EvalMessage]) -> list[Prediction]:
        return [self._predict_one(message) for message in messages]

    def _predict_one(self, message: EvalMessage) -> Prediction:
        started = time.perf_counter()
        text = normalize(message.text)
        barangay = find_barangay(text)
        asked_back = barangay is None and message.reply_if_asked is not None
        if asked_back:
            barangay = find_barangay(normalize(message.reply_if_asked or ""))
        return Prediction(
            message_id=message.id,
            priority=keyword_priority(text),
            case_key=message.sender,
            barangay=barangay,
            is_suspicious=any(word in text for word in SUSPICIOUS_WORDS + SPAM_WORDS),
            asked_back=asked_back,
            latency_s=time.perf_counter() - started,
            cost_usd=0.0,
        )


normalize = fold


def keyword_priority(text: str) -> Priority | None:
    if any(word in text for word in SPAM_WORDS + CLOSED_WORDS):
        return None
    for priority, words in PRIORITY_WORDS:
        if any(word in text for word in words):
            return priority
    return Priority.INFO


def find_barangay(text: str) -> str | None:
    """Deliberately naive substring match (the agents use domain.places.find_barangay)."""
    return next((name for alias, name in BARANGAY_SPELLINGS.items() if alias in text), None)
