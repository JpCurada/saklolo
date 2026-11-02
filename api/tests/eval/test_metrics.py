from saklolo.domain.models import MessageType, Priority
from saklolo.eval.metrics import Metric, compute_metrics
from saklolo.eval.types import GroundTruth, Prediction


def truth(
    message_id: str,
    priority: Priority | None,
    household_id: str | None = None,
    message_type: MessageType = MessageType.RESCUE,
    is_suspicious: bool = False,
) -> GroundTruth:
    return GroundTruth(
        message_id=message_id,
        message_type=message_type,
        priority=priority,
        is_suspicious=is_suspicious,
        household_id=household_id,
        barangay="Tumana" if household_id else None,
    )


def prediction(
    message_id: str,
    priority: Priority | None,
    case_key: str | None = None,
    is_suspicious: bool = False,
    latency_s: float = 0.0,
) -> Prediction:
    return Prediction(
        message_id=message_id,
        priority=priority,
        case_key=case_key,
        barangay="Tumana",
        is_suspicious=is_suspicious,
        latency_s=latency_s,
        cost_usd=0.001,
    )


def metric(metrics: list[Metric], name: str) -> Metric:
    return next(m for m in metrics if m.name == name)


def test_critical_recall_counts_missed_critical_cases() -> None:
    truths = [truth("a", Priority.CRITICAL), truth("b", Priority.CRITICAL)]
    predictions = [prediction("a", Priority.CRITICAL), prediction("b", Priority.HIGH)]

    result = metric(compute_metrics(truths, predictions), "Critical recall")

    assert result == Metric("Critical recall", 0.5, 2)


def test_recycled_posts_are_excluded_from_priority_metrics() -> None:
    truths = [
        truth("a", Priority.CRITICAL),
        truth("b", Priority.CRITICAL, message_type=MessageType.RECYCLED, is_suspicious=True),
    ]
    predictions = [prediction("a", Priority.CRITICAL), prediction("b", Priority.CRITICAL)]

    metrics = compute_metrics(truths, predictions)

    assert metric(metrics, "Critical precision") == Metric("Critical precision", 1.0, 1)
    assert metric(metrics, "Recycled flagged %").value == 0.0


def test_dedupe_scores_message_pairs() -> None:
    truths = [truth(i, Priority.HIGH, household_id="hh-1") for i in ("a", "b", "c")]
    predictions = [
        prediction("a", Priority.HIGH, case_key="x"),
        prediction("b", Priority.HIGH, case_key="x"),
        prediction("c", Priority.HIGH, case_key="y"),
    ]

    metrics = compute_metrics(truths, predictions)

    assert metric(metrics, "Dedupe precision") == Metric("Dedupe precision", 1.0, 1)
    assert metric(metrics, "Dedupe recall") == Metric("Dedupe recall", 1 / 3, 3)


def test_false_flag_rate_ignores_fake_messages() -> None:
    truths = [
        truth("a", Priority.HIGH, household_id="hh-1"),
        truth("b", None, message_type=MessageType.SPAM, is_suspicious=True),
    ]
    predictions = [
        prediction("a", Priority.HIGH, is_suspicious=True),
        prediction("b", None, is_suspicious=True),
    ]

    result = metric(compute_metrics(truths, predictions), "False-flag rate")

    assert result == Metric("False-flag rate", 1.0, 1)


def test_cost_and_latency_use_every_prediction() -> None:
    truths = [truth(i, Priority.INFO) for i in "abcd"]
    latencies = zip("abcd", [1, 2, 3, 9], strict=True)
    predictions = [prediction(i, Priority.INFO, latency_s=s) for i, s in latencies]

    metrics = compute_metrics(truths, predictions)

    assert metric(metrics, "p95 latency (s)").value == 9
    assert metric(metrics, "Cost per 10k messages (USD)").value == 10.0


def escalated(message_id: str, outcome: str, first: Priority, final: Priority) -> Prediction:
    return prediction(message_id, final).model_copy(
        update={
            "escalation_outcome": outcome,
            "escalation_agents": ["triage_reviewer"],
            "first_priority": first,
            "first_confidence": 0.5,
        }
    )


def test_swarm_metrics_count_escalations_and_changed_priorities() -> None:
    truths = [truth(f"m{i}", Priority.HIGH) for i in range(5)]
    predictions = [
        escalated("m0", "confirmed", Priority.HIGH, Priority.HIGH),
        escalated("m1", "raised", Priority.HIGH, Priority.CRITICAL),
        escalated("m2", "refused", Priority.HIGH, Priority.HIGH),
        prediction("m3", Priority.HIGH),
        prediction("m4", Priority.HIGH),
    ]

    metrics = compute_metrics(truths, predictions)

    assert metric(metrics, "Escalation rate") == Metric("Escalation rate", 0.6, 5)
    assert metric(metrics, "Swarm changed priority").value == 1 / 3
    assert metric(metrics, "Swarm confirmed") == Metric("Swarm confirmed", 1.0, 3)
    assert metric(metrics, "Swarm raised").value == 1.0
    assert metric(metrics, "Swarm refused").value == 1.0
    assert metric(metrics, "Swarm unavailable").value == 0.0


def test_swarm_metrics_are_undefined_without_escalations() -> None:
    metrics = compute_metrics([truth("m0", Priority.HIGH)], [prediction("m0", Priority.HIGH)])

    assert metric(metrics, "Escalation rate").value == 0.0
    assert metric(metrics, "Swarm changed priority").value is None
