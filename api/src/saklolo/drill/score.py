"""Score drill rounds against their answer keys and print the Drill table.

Each round is MODE KEY FILE: `manual` with the volunteer's sheet (CSV), or `saklolo`
with the API snapshot taken at the 15-minute mark (api_round export).

  uv run python -m saklolo.drill.score \\
    --round manual ../drill/keys/set-a-key.json ../drill/results/v1-manual.csv \\
    --round saklolo ../drill/keys/set-b-key.json ../drill/results/v1-saklolo.json

Definitions (drill/README.md):
- Critical case missed: a critical household with no message marked P1 in time.
- Messages triaged: messages given a priority within the window.
- Duplicate missed: a message filed under a different case than the rest of its
  household, among the messages that were triaged.
"""

import argparse
import csv
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

WINDOW_MIN = 15
PRIORITIES = {"P1", "P2", "P3", "P4"}


@dataclass(frozen=True)
class Filed:
    """How one message ended up: its priority, its case, and whether it was flagged."""

    priority: str | None
    case: str | None
    flagged: bool


@dataclass(frozen=True)
class RoundScore:
    mode: str
    set_name: str
    critical_total: int
    critical_missed: int
    messages_total: int
    triaged: int
    duplicates_total: int
    duplicates_missed: int
    recycled_total: int
    recycled_flagged: int


def score(mode: str, key: dict[str, Any], filed: dict[str, Filed]) -> RoundScore:
    households: dict[str, dict[str, Any]] = key["households"]
    in_set = set(key["messages"])
    triaged = {mid: f for mid, f in filed.items() if mid in in_set and f.priority in PRIORITIES}

    critical = [h for h in households.values() if h["critical"]]
    missed = sum(
        1
        for h in critical
        if not any(
            triaged.get(mid, Filed(None, None, False)).priority == "P1" for mid in h["message_ids"]
        )
    )

    duplicates_total = duplicates_missed = 0
    for household in households.values():
        cases = [triaged[mid].case for mid in household["message_ids"] if mid in triaged]
        if len(household["message_ids"]) < 2:
            continue
        duplicates_total += len(household["message_ids"]) - 1
        if len(cases) < 2:
            continue
        _, together = Counter(cases).most_common(1)[0]
        duplicates_missed += len(cases) - together

    recycled = key["recycled"]
    return RoundScore(
        mode=mode,
        set_name=key["set"],
        critical_total=len(critical),
        critical_missed=missed,
        messages_total=len(key["messages"]),
        triaged=len(triaged),
        duplicates_total=duplicates_total,
        duplicates_missed=duplicates_missed,
        recycled_total=len(recycled),
        recycled_flagged=sum(
            1 for mid in recycled if filed.get(mid, Filed(None, None, False)).flagged
        ),
    )


def read_manual(path: Path, window: int = WINDOW_MIN) -> dict[str, Filed]:
    """The volunteer's sheet. Rows filed after the window count as not triaged."""
    filed: dict[str, Filed] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            message_id = (row.get("message_id") or "").strip()
            if not message_id:
                continue
            minute = _number(row.get("minute"))
            in_time = minute is not None and minute <= window
            priority = (row.get("priority") or "").strip().upper()
            filed[message_id] = Filed(
                priority=priority if in_time and priority in PRIORITIES else None,
                case=(row.get("case_label") or "").strip().casefold() or None,
                flagged=(row.get("suspicious") or "").strip().upper() in {"Y", "YES", "1", "TRUE"},
            )
    return filed


def read_saklolo(path: Path, key: dict[str, Any]) -> dict[str, Filed]:
    """The API snapshot, matched back to drill message IDs by sender and text."""
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    by_text = _message_index(key)
    final_priority = {case["case_id"]: case["priority"] for case in snapshot["cases"]}
    filed: dict[str, Filed] = {}
    for record in snapshot["messages"]:
        message = record["message"]
        message_id = by_text.get((message["sender"], message["text"]))
        if message_id is None:
            continue
        outcome = record.get("outcome") or {}
        case_id = record.get("case_id")
        # The dispatcher's final word on the case wins over the first triage.
        priority = final_priority.get(case_id) if case_id else outcome.get("priority")
        filed[message_id] = Filed(
            priority=priority or outcome.get("priority"),
            case=case_id,
            flagged=bool(outcome.get("is_suspicious")),
        )
    return filed


def _message_index(key: dict[str, Any]) -> dict[tuple[str, str], str]:
    index = key.get("index")
    if not isinstance(index, dict):
        raise ValueError("Answer key has no sender/text index; rebuild it with drill.sets.")
    return {(row["sender"], row["text"]): mid for mid, row in index.items()}


def _number(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def table(rounds: list[RoundScore]) -> str:
    def total(mode: str) -> dict[str, int]:
        picked = [r for r in rounds if r.mode == mode]
        fields = [
            "critical_total",
            "critical_missed",
            "messages_total",
            "triaged",
            "duplicates_total",
            "duplicates_missed",
        ]
        return {f: sum(getattr(r, f) for r in picked) for f in fields} | {"rounds": len(picked)}

    manual, saklolo = total("manual"), total("saklolo")

    def cell(t: dict[str, int], part: str, whole: str) -> str:
        return f"{t[part]} of {t[whole]}" if t["rounds"] else "n/a"

    lines = [
        "| Measure | Manual | Saklolo |",
        "|---|---|---|",
        f"| Critical cases missed | {cell(manual, 'critical_missed', 'critical_total')} "
        f"| {cell(saklolo, 'critical_missed', 'critical_total')} |",
        f"| Messages triaged in {WINDOW_MIN} min | {cell(manual, 'triaged', 'messages_total')} "
        f"| {cell(saklolo, 'triaged', 'messages_total')} |",
        f"| Duplicates missed | {cell(manual, 'duplicates_missed', 'duplicates_total')} "
        f"| {cell(saklolo, 'duplicates_missed', 'duplicates_total')} |",
        "",
        f"Rounds: {manual['rounds']} manual, {saklolo['rounds']} with Saklolo.",
    ]
    for r in rounds:
        lines.append(
            f"- {r.mode} on {r.set_name}: critical missed {r.critical_missed}/{r.critical_total}, "
            f"triaged {r.triaged}/{r.messages_total}, duplicates missed "
            f"{r.duplicates_missed}/{r.duplicates_total}, recycled flagged "
            f"{r.recycled_flagged}/{r.recycled_total}"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--round", nargs=3, action="append", metavar=("MODE", "KEY", "FILE"), required=True
    )
    args = parser.parse_args()
    rounds = []
    for mode, key_path, file_path in args.round:
        if mode not in {"manual", "saklolo"}:
            raise SystemExit(f"Unknown mode {mode!r}: use manual or saklolo")
        key = json.loads(Path(key_path).read_text(encoding="utf-8"))
        filed = (
            read_manual(Path(file_path)) if mode == "manual" else read_saklolo(Path(file_path), key)
        )
        rounds.append(score(mode, key, filed))
    print(table(rounds))


if __name__ == "__main__":
    main()
