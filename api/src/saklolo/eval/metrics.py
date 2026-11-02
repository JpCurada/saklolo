"""Metric definitions (ai-engineering rules: Critical recall is the headline).

Populations:
- Priority metrics: messages with a true priority, excluding recycled posts
  (those are scored by the verification metrics instead).
- Dedupe and barangay: messages that belong to a real household.
- False-flag rate: real messages (not recycled, not spam).
- Swarm metrics: every message for the escalation rate; escalated messages for the
  rest. Outcome counts are counts, not rates.
"""

import math
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from itertools import combinations

from saklolo.agents.state import EscalationOutcome
from saklolo.domain.models import MessageType, Priority
from saklolo.eval.types import GroundTruth, Prediction

FAKE_TYPES = {MessageType.RECYCLED, MessageType.SPAM}


@dataclass(frozen=True)
class Metric:
    name: str
    value: float | None  # None when the population is empty or the metric is undefined
    n: int


Pair = tuple[GroundTruth, Prediction]


def compute_metrics(truths: list[GroundTruth], predictions: list[Prediction]) -> list[Metric]:
    pairs = _join(truths, predictions)
    priority_pairs = [
        (t, p)
        for t, p in pairs
        if t.priority is not None and t.message_type != MessageType.RECYCLED
    ]
    household_pairs = [(t, p) for t, p in pairs if t.household_id is not None]
    return [
        critical_recall(priority_pairs),
        critical_precision(priority_pairs),
        macro_f1(priority_pairs),
        *dedupe_precision_recall(household_pairs),
        barangay_accuracy(household_pairs),
        ask_back_rate(predictions),
        false_flag_rate(pairs),
        recycled_flagged_rate(pairs),
        p95_latency(predictions),
        cost_per_10k(predictions),
        escalation_rate(predictions),
        swarm_changed_rate(predictions),
        *swarm_outcome_counts(predictions),
    ]


def critical_recall(pairs: list[Pair]) -> Metric:
    critical = [p for t, p in pairs if t.priority == Priority.CRITICAL]
    return _rate("Critical recall", [p.priority == Priority.CRITICAL for p in critical])


def critical_precision(pairs: list[Pair]) -> Metric:
    flagged = [t for t, p in pairs if p.priority == Priority.CRITICAL]
    return _rate("Critical precision", [t.priority == Priority.CRITICAL for t in flagged])


def macro_f1(pairs: list[Pair]) -> Metric:
    scores = [_f1(pairs, level) for level in Priority]
    return Metric("Macro-F1 (priority)", sum(scores) / len(scores) if pairs else None, len(pairs))


def dedupe_precision_recall(pairs: list[Pair]) -> list[Metric]:
    """Pairwise: two messages are 'together' if they share a household / a case key."""
    true_together = _together(pairs, lambda t, _: t.household_id)
    predicted_together = _together(pairs, lambda _, p: p.case_key)
    hits = len(true_together & predicted_together)
    return [
        Metric("Dedupe precision", _ratio(hits, len(predicted_together)), len(predicted_together)),
        Metric("Dedupe recall", _ratio(hits, len(true_together)), len(true_together)),
    ]


def barangay_accuracy(pairs: list[Pair]) -> Metric:
    return _rate("Correct barangay %", [t.barangay == p.barangay for t, p in pairs])


def ask_back_rate(predictions: list[Prediction]) -> Metric:
    """How often residents were asked for their location: lower is better, if accuracy holds."""
    return _rate("Ask-back rate", [p.asked_back for p in predictions])


def false_flag_rate(pairs: list[Pair]) -> Metric:
    real = [p for t, p in pairs if t.message_type not in FAKE_TYPES]
    return _rate("False-flag rate", [p.is_suspicious for p in real])


def recycled_flagged_rate(pairs: list[Pair]) -> Metric:
    recycled = [p for t, p in pairs if t.message_type == MessageType.RECYCLED]
    return _rate("Recycled flagged %", [p.is_suspicious for p in recycled])


def p95_latency(predictions: list[Prediction]) -> Metric:
    latencies = sorted(p.latency_s for p in predictions)
    if not latencies:
        return Metric("p95 latency (s)", None, 0)
    index = max(0, math.ceil(0.95 * len(latencies)) - 1)  # nearest-rank percentile
    return Metric("p95 latency (s)", latencies[index], len(latencies))


def cost_per_10k(predictions: list[Prediction]) -> Metric:
    total = sum(p.cost_usd for p in predictions)
    value = total / len(predictions) * 10_000 if predictions else None
    return Metric("Cost per 10k messages (USD)", value, len(predictions))


def escalation_rate(predictions: list[Prediction]) -> Metric:
    return _rate("Escalation rate", [p.escalated for p in predictions])


def swarm_changed_rate(predictions: list[Prediction]) -> Metric:
    """Among escalated messages: how often the final priority differs from triage's."""
    escalated = [p for p in predictions if p.escalated]
    return _rate("Swarm changed priority", [p.priority != p.first_priority for p in escalated])


def swarm_outcome_counts(predictions: list[Prediction]) -> list[Metric]:
    escalated = [p for p in predictions if p.escalated]
    return [
        Metric(
            f"Swarm {outcome.value}",
            float(sum(p.escalation_outcome == outcome for p in escalated)),
            len(escalated),
        )
        for outcome in EscalationOutcome
    ]


def _join(truths: list[GroundTruth], predictions: list[Prediction]) -> list[Pair]:
    by_id = {p.message_id: p for p in predictions}
    missing = [t.message_id for t in truths if t.message_id not in by_id]
    if missing:
        raise ValueError(f"no prediction for {len(missing)} messages, e.g. {missing[:3]}")
    return [(t, by_id[t.message_id]) for t in truths]


def _f1(pairs: list[Pair], level: Priority) -> float:
    true_positive = sum(t.priority == level and p.priority == level for t, p in pairs)
    predicted = sum(p.priority == level for _, p in pairs)
    actual = sum(t.priority == level for t, _ in pairs)
    if predicted + actual == 0:
        return 0.0
    return 2 * true_positive / (predicted + actual)


def _together(
    pairs: list[Pair], key_of: Callable[[GroundTruth, Prediction], str | None]
) -> set[frozenset[str]]:
    groups: dict[str, list[str]] = {}
    for truth, prediction in pairs:
        key = key_of(truth, prediction)
        if key is not None:
            groups.setdefault(key, []).append(truth.message_id)
    return {frozenset(pair) for ids in groups.values() for pair in combinations(ids, 2)}


def _rate(name: str, outcomes: Iterable[bool]) -> Metric:
    outcomes = list(outcomes)
    return Metric(name, _ratio(sum(outcomes), len(outcomes)), len(outcomes))


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None
