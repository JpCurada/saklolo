from typing import Any

import pytest

from saklolo.dataset.io import Dataset
from saklolo.dataset.schema import DatasetMessage
from saklolo.domain.models import Priority
from saklolo.eval.ground_truth import GroundTruthSource, MissingLabelsError, ground_truth


def unlabeled_message() -> DatasetMessage:
    row: dict[str, Any] = {
        "id": "msg-0001",
        "split": "dev",
        "scenario_hour": 9,
        "channel": "sms",
        "sender": "+639000000001",
        "text": "nasa bubong na kami",
        "ask_back_reply": None,
        "truth": {
            "message_type": "relief_info",
            "household_id": None,
            "recycled_from": None,
            "location_resolvable": True,
        },
        "labels": None,
        "label_meta": {"status": "pending", "rubric_version": "1.0"},
        "generator_intent": {"priority": "P4"},
    }
    return DatasetMessage.model_validate(row)


EMPTY = Dataset(households=[], messages=[], archive=[])


def test_scoring_against_missing_labels_fails_loudly() -> None:
    with pytest.raises(MissingLabelsError):
        ground_truth(EMPTY, [unlabeled_message()], GroundTruthSource.LABELS)


def test_intent_source_is_allowed_for_provisional_runs() -> None:
    [result] = ground_truth(EMPTY, [unlabeled_message()], GroundTruthSource.INTENT)

    assert result.priority == Priority.INFO
