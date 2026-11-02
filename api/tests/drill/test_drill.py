"""Drill sets are balanced and reproducible; scoring counts what the README defines."""

import json
from pathlib import Path

from saklolo.config import REPO_ROOT
from saklolo.dataset.io import load_dataset
from saklolo.dataset.schema import DatasetMessage
from saklolo.drill.score import Filed, read_manual, read_saklolo, score
from saklolo.drill.sets import build_sets


def dev_messages() -> list[DatasetMessage]:
    dataset, problems = load_dataset(REPO_ROOT / "data")
    assert problems == []
    return [m for m in dataset.messages if m.split == "dev"]


def counts(key: dict) -> tuple[int, int, int]:
    households = key["households"].values()
    critical = sum(1 for h in households if h["critical"])
    duplicates = sum(len(h["message_ids"]) - 1 for h in households)
    return critical, duplicates, len(key["recycled"])


def test_sets_use_every_message_once_and_never_split_a_household() -> None:
    messages = dev_messages()
    sets = build_sets(messages)

    ids = [m.id for s in sets for m in s.messages]
    assert sorted(ids) == sorted(m.id for m in messages)
    homes = [set(s.key()["households"]) for s in sets]
    assert homes[0].isdisjoint(homes[1])


def test_sets_are_equivalent_in_size_and_difficulty() -> None:
    a, b = (s.key() for s in build_sets(dev_messages()))

    assert abs(len(a["messages"]) - len(b["messages"])) <= 6
    for left, right in zip(counts(a), counts(b), strict=True):
        assert abs(left - right) <= 3


def test_the_same_seed_gives_the_same_sets() -> None:
    first = [[m.id for m in s.messages] for s in build_sets(dev_messages(), seed=7)]
    again = [[m.id for m in s.messages] for s in build_sets(dev_messages(), seed=7)]

    assert first == again


KEY = {
    "set": "set-x",
    "messages": ["m1", "m2", "m3", "m4", "m5"],
    "households": {
        "hh-1": {"critical": True, "message_ids": ["m1", "m2"]},
        "hh-2": {"critical": True, "message_ids": ["m3"]},
        "hh-3": {"critical": False, "message_ids": ["m4"]},
    },
    "recycled": ["m5"],
    "index": {
        "m1": {"sender": "+639000000001", "text": "nasa bubong kami"},
        "m2": {"sender": "+639000000002", "text": "pamilya ko nasa bubong"},
        "m3": {"sender": "+639000000003", "text": "tulong po"},
        "m4": {"sender": "+639000000004", "text": "lumikas kami"},
        "m5": {"sender": "+639000000005", "text": "Nov 12 2020 share"},
    },
}


def test_manual_scoring_counts_misses_late_rows_and_split_duplicates(tmp_path: Path) -> None:
    sheet = tmp_path / "manual.csv"
    sheet.write_text(
        "message_id,minute,case_label,priority,suspicious\n"
        "m1,3,A,P1,\n"
        "m2,6,B,P2,\n"  # same household, filed as a different case
        "m3,16,C,P1,\n"  # critical, but after the window
        "m4,9,D,P3,\n"
        "m5,12,E,P2,Y\n",
        encoding="utf-8",
    )

    result = score("manual", KEY, read_manual(sheet))

    assert (result.critical_missed, result.critical_total) == (1, 2)
    assert (result.triaged, result.messages_total) == (4, 5)
    assert (result.duplicates_missed, result.duplicates_total) == (1, 1)
    assert (result.recycled_flagged, result.recycled_total) == (1, 1)


def record(mid: str, case: str | None, priority: str | None, flagged: bool = False) -> dict:
    row = KEY["index"][mid]  # type: ignore[index]
    return {
        "message": {"sender": row["sender"], "text": row["text"]},
        "case_id": case,
        "outcome": {"priority": priority, "is_suspicious": flagged},
    }


def test_saklolo_scoring_uses_the_dispatchers_final_priority(tmp_path: Path) -> None:
    snapshot = {
        "messages": [
            record("m1", "case-0001", "P2"),
            record("m2", "case-0001", "P2"),
            record("m3", "case-0002", "P1"),
            record("m4", "case-0003", "P3"),
            record("m5", "case-0004", "P2", flagged=True),
        ],
        # The dispatcher raised case-0001 to P1.
        "cases": [
            {"case_id": "case-0001", "priority": "P1"},
            {"case_id": "case-0002", "priority": "P1"},
            {"case_id": "case-0003", "priority": "P3"},
            {"case_id": "case-0004", "priority": "P2"},
        ],
    }
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot), encoding="utf-8")

    result = score("saklolo", KEY, read_saklolo(path, KEY))

    assert result.critical_missed == 0
    assert result.duplicates_missed == 0
    assert result.triaged == 5
    assert result.recycled_flagged == 1


def test_an_unknown_message_is_not_counted() -> None:
    result = score("manual", KEY, {"zz": Filed("P1", "a", False)})

    assert result.triaged == 0
    assert result.critical_missed == 2
