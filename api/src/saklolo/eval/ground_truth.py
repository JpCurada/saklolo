"""Build eval inputs and ground truth from the dataset."""

from enum import StrEnum

from saklolo.dataset.io import Dataset
from saklolo.dataset.schema import DatasetMessage, Labels
from saklolo.eval.types import EvalMessage, GroundTruth


class GroundTruthSource(StrEnum):
    LABELS = "labels"  # adjudicated human labels: the only source for reported numbers
    INTENT = "intent"  # generator intent: provisional, for iterating before labeling


class MissingLabelsError(Exception):
    def __init__(self, unlabeled: int) -> None:
        super().__init__(
            f"{unlabeled} messages have no human labels yet. Label them "
            "or pass --ground-truth intent for a "
            "provisional score."
        )


def split_messages(dataset: Dataset, split: str) -> list[DatasetMessage]:
    """Messages in one split, in timeline order."""
    selected = [m for m in dataset.messages if m.split == split]
    return sorted(selected, key=lambda m: (m.scenario_hour, m.id))


def to_eval_message(message: DatasetMessage) -> EvalMessage:
    return EvalMessage(
        id=message.id,
        sender=message.sender,
        channel=message.channel,
        scenario_hour=message.scenario_hour,
        text=message.text,
        reply_if_asked=message.ask_back_reply,
    )


def ground_truth(
    dataset: Dataset, messages: list[DatasetMessage], source: GroundTruthSource
) -> list[GroundTruth]:
    unlabeled = sum(m.labels is None for m in messages)
    if source == GroundTruthSource.LABELS and unlabeled:
        raise MissingLabelsError(unlabeled)

    barangay_by_household = {h.household_id: h.barangay for h in dataset.households}
    truths = []
    for message in messages:
        labels: Labels = message.generator_intent
        if source == GroundTruthSource.LABELS and message.labels is not None:
            labels = message.labels
        household_id = message.truth.household_id
        truths.append(
            GroundTruth(
                message_id=message.id,
                message_type=message.truth.message_type,
                priority=labels.priority,
                is_suspicious=labels.is_suspicious,
                household_id=household_id,
                barangay=barangay_by_household.get(household_id) if household_id else None,
            )
        )
    return truths
