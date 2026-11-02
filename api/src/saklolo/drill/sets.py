"""Split the dev messages into two equivalent drill sets, with an answer key for each.

Households are never split across sets, so every duplicate stays with its original.
Households are balanced by whether they are critical and whether they sent more than
one message; messages without a household (recycled, spam, relief) are balanced by
type. The same seed always gives the same sets.

Priorities come from the generator's intent until human labels exist, so the keys
are provisional in the same way the dev eval is.

Run: uv run python -m saklolo.drill.sets [--seed 2026] [--out ../drill]
"""

import argparse
import csv
import json
import random
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from saklolo.config import REPO_ROOT
from saklolo.dataset.io import load_dataset
from saklolo.dataset.scenario import scenario_time
from saklolo.dataset.schema import DatasetMessage
from saklolo.domain.models import MessageType, Priority

SET_NAMES = ("set-a", "set-b")
DEFAULT_SEED = 2026


@dataclass
class DrillSet:
    name: str
    messages: list[DatasetMessage] = field(default_factory=list)

    def key(self) -> dict[str, object]:
        """What scoring checks against: households, which are critical, and old posts."""
        message_ids: dict[str, list[str]] = defaultdict(list)
        critical: set[str] = set()
        for message in self.messages:
            household_id = message.truth.household_id
            if household_id is None:
                continue
            message_ids[household_id].append(message.id)
            if message.generator_intent.priority == Priority.CRITICAL:
                critical.add(household_id)
        households = {
            hid: {"critical": hid in critical, "message_ids": ids}
            for hid, ids in message_ids.items()
        }
        recycled = [m.id for m in self.messages if m.truth.message_type == MessageType.RECYCLED]
        return {
            "set": self.name,
            "provisional": "Priorities are the generator's intent until human labels exist.",
            "messages": [m.id for m in self.messages],
            "households": households,
            "recycled": recycled,
            # Lets scoring match the API's messages back to drill IDs.
            "index": {m.id: {"sender": m.sender, "text": m.text} for m in self.messages},
        }


def build_sets(messages: list[DatasetMessage], seed: int = DEFAULT_SEED) -> list[DrillSet]:
    # Reproducible shuffling for a fair split, not security.
    rng = random.Random(seed)  # noqa: S311
    sets = [DrillSet(name) for name in SET_NAMES]
    for stratum in _households_by_stratum(messages) + _loose_by_type(messages):
        rng.shuffle(stratum)
        # Larger households first, so the small ones can even out the message count.
        stratum.sort(key=len, reverse=True)
        taken = [0, 0]
        for unit in stratum:
            # Balance this stratum first, then the total number of messages.
            pick = min((0, 1), key=lambda i: (taken[i], len(sets[i].messages)))
            sets[pick].messages.extend(unit)
            taken[pick] += 1
    for drill_set in sets:
        drill_set.messages.sort(key=lambda m: (m.scenario_hour, m.id))
    return sets


Unit = list[DatasetMessage]  # a household's messages, or one message without a household


def _households_by_stratum(messages: list[DatasetMessage]) -> list[list[Unit]]:
    """Households grouped by (critical, sent more than one message), in a fixed order."""
    by_household: dict[str, Unit] = defaultdict(list)
    for message in messages:
        if message.truth.household_id:
            by_household[message.truth.household_id].append(message)
    strata: dict[tuple[bool, bool], list[Unit]] = defaultdict(list)
    for household_id in sorted(by_household):
        group = by_household[household_id]
        critical = any(m.generator_intent.priority == Priority.CRITICAL for m in group)
        strata[(critical, len(group) > 1)].append(group)
    return [strata[key] for key in sorted(strata)]


def _loose_by_type(messages: list[DatasetMessage]) -> list[list[Unit]]:
    """Messages without a household (recycled, spam, relief), grouped by type."""
    by_type: dict[str, list[Unit]] = defaultdict(list)
    for message in sorted(messages, key=lambda m: m.id):
        if not message.truth.household_id:
            by_type[message.truth.message_type.value].append([message])
    return [by_type[key] for key in sorted(by_type)]


def write_sets(sets: list[DrillSet], out: Path) -> None:
    (out / "sets").mkdir(parents=True, exist_ok=True)
    (out / "keys").mkdir(parents=True, exist_ok=True)
    for drill_set in sets:
        # The sheet volunteers read: what a messy group chat export looks like.
        with (out / "sets" / f"{drill_set.name}.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["message_id", "received", "channel", "sender", "text"])
            for m in drill_set.messages:
                received = scenario_time(m.scenario_hour).strftime("%b %d %H:%M")
                writer.writerow([m.id, received, m.channel.value, m.sender, m.text])
        # The feed for the Saklolo round, in arrival order.
        with (out / "sets" / f"{drill_set.name}.jsonl").open("w", encoding="utf-8") as f:
            for m in drill_set.messages:
                row = {
                    "id": m.id,
                    "scenario_hour": m.scenario_hour,
                    "channel": m.channel.value,
                    "sender": m.sender,
                    "text": m.text,
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        key_path = out / "keys" / f"{drill_set.name}-key.json"
        key_path.write_text(json.dumps(drill_set.key(), indent=2) + "\n", encoding="utf-8")


def summary(drill_set: DrillSet) -> str:
    key = drill_set.key()
    households = cast(dict[str, dict[str, Any]], key["households"])
    recycled = cast(list[str], key["recycled"])
    critical = sum(1 for h in households.values() if h["critical"])
    duplicates = sum(len(h["message_ids"]) - 1 for h in households.values())
    return (
        f"{drill_set.name}: {len(drill_set.messages)} messages, {len(households)} households, "
        f"{critical} critical, {duplicates} duplicate messages, {len(recycled)} recycled"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "drill")
    args = parser.parse_args()
    dataset, problems = load_dataset(REPO_ROOT / "data")
    if problems:
        raise SystemExit("Dataset is invalid; run `python -m saklolo.dataset.validate`.")
    dev = [m for m in dataset.messages if m.split == "dev"]
    sets = build_sets(dev, args.seed)
    write_sets(sets, args.out)
    for drill_set in sets:
        print(summary(drill_set))


if __name__ == "__main__":
    main()
