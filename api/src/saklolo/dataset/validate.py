"""Validate data/*.jsonl against docs/dataset-spec.md §11.

Usage: uv run python -m saklolo.dataset.validate [--data-dir PATH]
Exits non-zero and lists every problem if the dataset is invalid.
"""

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from saklolo.config import REPO_ROOT
from saklolo.dataset.io import load_dataset
from saklolo.dataset.schema import ArchivePost, DatasetMessage, Household, Labels
from saklolo.domain.models import MessageType, StatusUpdateKind
from saklolo.domain.places import MARIKINA_BARANGAYS

# docs/dataset-spec.md §4
TARGET_MIX: dict[str, dict[MessageType, int]] = {
    "dev": {
        MessageType.RESCUE: 60,
        MessageType.STATUS_UPDATE: 22,
        MessageType.DUPLICATE: 23,
        MessageType.RELIEF_INFO: 15,
        MessageType.VAGUE_LOCATION: 15,
        MessageType.RECYCLED: 8,
        MessageType.SPAM: 7,
    },
    "eval": {
        MessageType.RESCUE: 160,
        MessageType.STATUS_UPDATE: 60,
        MessageType.DUPLICATE: 60,
        MessageType.RELIEF_INFO: 40,
        MessageType.VAGUE_LOCATION: 40,
        MessageType.RECYCLED: 20,
        MessageType.SPAM: 20,
    },
    "calibration": {
        MessageType.RESCUE: 20,
        MessageType.STATUS_UPDATE: 8,
        MessageType.DUPLICATE: 7,
        MessageType.RELIEF_INFO: 5,
        MessageType.VAGUE_LOCATION: 5,
        MessageType.RECYCLED: 3,
        MessageType.SPAM: 2,
    },
}
MIX_TOLERANCE = 2

NEEDS_HOUSEHOLD = {
    MessageType.RESCUE,
    MessageType.DUPLICATE,
    MessageType.VAGUE_LOCATION,
    MessageType.STATUS_UPDATE,
}
NO_HOUSEHOLD = {MessageType.RECYCLED, MessageType.SPAM}
FIRST_REPORT = {MessageType.RESCUE, MessageType.VAGUE_LOCATION}

PHONE_IN_TEXT = re.compile(r"(?:\+63|0)9\d{9}")
FAKE_PHONE_IN_TEXT = re.compile(r"(?:\+63|0)9000000\d{3}")


def find_problems(
    households: list[Household],
    messages: list[DatasetMessage],
    archive: list[ArchivePost],
) -> list[str]:
    """Cross-row consistency checks. Schema checks happen at parse time."""
    by_id = {h.household_id: h for h in households}
    archive_ids = {a.archive_id for a in archive}
    problems = [*_duplicate_ids(households, messages, archive)]
    problems += [p for h in households for p in _household_problems(h)]
    problems += [p for m in messages for p in _message_problems(m, by_id, archive_ids)]
    problems += _ordering_problems(messages)
    problems += _split_leaks(messages)
    return problems


def check_mix(messages: list[DatasetMessage]) -> list[str]:
    """Type counts per split must stay within MIX_TOLERANCE of the spec."""
    problems = []
    counts = Counter((m.split, m.truth.message_type) for m in messages)
    for split in {m.split for m in messages}:
        for message_type, target in TARGET_MIX[split].items():
            actual = counts[(split, message_type)]
            if abs(actual - target) > MIX_TOLERANCE:
                problems.append(f"{split}: {actual} {message_type} messages, expected {target}")
    return problems


def _duplicate_ids(
    households: list[Household], messages: list[DatasetMessage], archive: list[ArchivePost]
) -> list[str]:
    ids = (
        [h.household_id for h in households]
        + [m.id for m in messages]
        + [a.archive_id for a in archive]
    )
    return [f"duplicate id {i}" for i, n in Counter(ids).items() if n > 1]


def _household_problems(household: Household) -> list[str]:
    if household.barangay not in MARIKINA_BARANGAYS:
        return [f"{household.household_id}: unknown barangay {household.barangay!r}"]
    return []


def _message_problems(
    message: DatasetMessage, households: dict[str, Household], archive_ids: set[str]
) -> list[str]:
    problems = [
        *_household_link_problems(message, households),
        *_recycled_problems(message, archive_ids),
        *_ask_back_problems(message),
        *_phone_problems(message),
    ]
    kind = message.truth.message_type
    for name, labels in (
        ("generator_intent", message.generator_intent),
        ("labels", message.labels),
    ):
        if labels is not None:
            problems += [f"{name}: {p}" for p in label_problems(kind, labels)]
    return [f"{message.id}: {p}" for p in problems]


def _household_link_problems(
    message: DatasetMessage, households: dict[str, Household]
) -> list[str]:
    truth = message.truth
    household = households.get(truth.household_id) if truth.household_id else None
    problems = []
    if truth.message_type in NEEDS_HOUSEHOLD and household is None:
        problems.append(f"{truth.message_type} needs an existing household_id")
    if truth.message_type in NO_HOUSEHOLD and truth.household_id is not None:
        problems.append(f"{truth.message_type} must not have a household_id")
    if household and message.sender not in household.senders:
        problems.append(f"sender is not listed for {household.household_id}")
    return problems


def _recycled_problems(message: DatasetMessage, archive_ids: set[str]) -> list[str]:
    recycled_from = message.truth.recycled_from
    problems = []
    if (message.truth.message_type == MessageType.RECYCLED) != (recycled_from is not None):
        problems.append("recycled_from is set iff message_type is recycled")
    if recycled_from and recycled_from not in archive_ids:
        problems.append(f"unknown archive post {recycled_from}")
    return problems


def _ask_back_problems(message: DatasetMessage) -> list[str]:
    if message.truth.message_type != MessageType.VAGUE_LOCATION:
        has_reply = message.ask_back_reply is not None
        return ["only vague_location messages have ask_back_reply"] if has_reply else []
    if not message.ask_back_reply or message.truth.location_resolvable:
        return ["vague_location needs ask_back_reply and resolvable=false"]
    return []


def _phone_problems(message: DatasetMessage) -> list[str]:
    unfaked = [p for p in PHONE_IN_TEXT.findall(message.text) if not FAKE_PHONE_IN_TEXT.match(p)]
    return [f"phone-like numbers outside the fake range: {unfaked}"] if unfaked else []


def label_problems(kind: MessageType, labels: Labels) -> list[str]:
    closes_case = labels.status_update_kind == StatusUpdateKind.RESCUED
    may_lack_priority = kind == MessageType.SPAM or closes_case
    problems = []
    if labels.priority is None and not may_lack_priority:
        problems.append("priority is required")
    if labels.priority is not None and may_lack_priority:
        problems.append("priority must be null for spam and rescued updates")
    if (kind == MessageType.STATUS_UPDATE) != (labels.status_update_kind is not None):
        problems.append("status_update_kind is set iff message_type is status_update")
    if labels.is_suspicious != bool(labels.suspicion_reasons):
        problems.append("is_suspicious and suspicion_reasons disagree")
    return problems


def _ordering_problems(messages: list[DatasetMessage]) -> list[str]:
    """Duplicates and status updates must follow a first report of their household."""
    first_report: dict[str, float] = {}
    for m in messages:
        if m.truth.message_type in FIRST_REPORT and m.truth.household_id:
            hour = first_report.get(m.truth.household_id, m.scenario_hour)
            first_report[m.truth.household_id] = min(hour, m.scenario_hour)

    follow_ups = {MessageType.DUPLICATE, MessageType.STATUS_UPDATE}
    problems = []
    for m in messages:
        household_id = m.truth.household_id
        if m.truth.message_type not in follow_ups or household_id is None:
            continue
        reported_at = first_report.get(household_id)
        if reported_at is None or reported_at >= m.scenario_hour:
            problems.append(f"{m.id}: no earlier rescue/vague_location for {household_id}")
    return problems


def _split_leaks(messages: list[DatasetMessage]) -> list[str]:
    splits_by_household: dict[str, set[str]] = defaultdict(set)
    for m in messages:
        if m.truth.household_id:
            splits_by_household[m.truth.household_id].add(m.split)
    return [
        f"{household_id} appears in several splits: {sorted(splits)}"
        for household_id, splits in splits_by_household.items()
        if len(splits) > 1
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data")
    data_dir: Path = parser.parse_args().data_dir

    dataset, problems = load_dataset(data_dir)
    problems += find_problems(dataset.households, dataset.messages, dataset.archive)
    problems += check_mix(dataset.messages)

    for problem in problems:
        print(problem, file=sys.stderr)
    counts = f"{len(dataset.messages)} messages, {len(dataset.households)} households"
    print(f"{counts}, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
