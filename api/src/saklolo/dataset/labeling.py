"""Human labeling for data/messages.jsonl.

Three steps, each a subcommand:

  export  Write a blank labeling sheet (CSV) for one split. Labelers see the message
          only: never generator_intent, truth.*, the other labeler, or a model.
  agree   Compare two filled sheets: Cohen's kappa for priority (also linearly
          weighted) and message type, percent agreement per field, and a
          disagreements sheet to adjudicate.
  apply   Write the agreed and adjudicated answers into the `labels` field, keep both
          labelers' answers in `label_meta`, and report where the labelers disagree
          with the generator's truth.* (reported, never silently fixed).

Usage: uv run python -m saklolo.dataset.labeling {export,agree,apply} --help
"""

import argparse
import csv
import json
import sys
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from saklolo.config import REPO_ROOT
from saklolo.dataset.io import load_jsonl
from saklolo.dataset.schema import DatasetMessage, LabelMeta, Labels
from saklolo.dataset.validate import label_problems
from saklolo.domain.models import (
    MessageType,
    Priority,
    StatusUpdateKind,
    SuspicionReason,
    Vulnerability,
    WaterLevel,
)

MESSAGES = REPO_ROOT / "data" / "messages.jsonl"
RUBRIC_VERSION = "1.0"

# Shown to the labeler, read-only.
CONTEXT_COLUMNS = ["id", "channel", "scenario_hour", "text", "ask_back_reply"]
# Filled in by the labeler. Lists use ";" ("infant;senior"); yes/no for booleans.
LABEL_COLUMNS = [
    "priority",
    "message_type",
    "people_count",
    "vulnerable",
    "water_level",
    "medical_emergency",
    "status_update_kind",
    "is_suspicious",
    "suspicion_reasons",
    "location_resolvable",
    "same_household_as",
    "notes",
]
# Fields compared between labelers. Notes are free text and never compared.
COMPARED = [c for c in LABEL_COLUMNS if c != "notes"]
NO_PRIORITY = "none"  # spam and "we're safe" updates have no priority


class SheetError(ValueError):
    """A sheet row can't be read; the message names the id and the column."""


# --- export


def export_sheet(messages: Iterable[DatasetMessage], split: str, out: Path) -> int:
    rows = [m for m in messages if m.split == split]
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(CONTEXT_COLUMNS + LABEL_COLUMNS)
        for m in rows:
            context = [m.id, m.channel, m.scenario_hour, m.text, m.ask_back_reply or ""]
            writer.writerow(context + [""] * len(LABEL_COLUMNS))
    return len(rows)


# --- reading sheets


@dataclass(frozen=True)
class Answer:
    """One labeler's answer for one message, normalized for comparison."""

    message_id: str
    fields: dict[str, str]
    notes: str


def read_sheet(path: Path) -> dict[str, Answer]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        missing = [c for c in ["id", *LABEL_COLUMNS] if c not in (reader.fieldnames or [])]
        if missing:
            raise SheetError(f"{path.name}: missing columns {missing}")
        answers = {}
        for row in reader:
            message_id = row["id"].strip()
            fields = {name: normalize(name, row[name], message_id) for name in COMPARED}
            answers[message_id] = Answer(message_id, fields, row["notes"].strip())
    return answers


def normalize(field: str, raw: str | None, message_id: str) -> str:
    """Canonical text for one cell, so "P1" and " p1 " compare equal."""
    value = (raw or "").strip()
    try:
        return _NORMALIZE.get(field, str.strip)(value)
    except ValueError as error:
        raise SheetError(f"{message_id}: {field}={raw!r}: {error}") from None


def _priority(value: str) -> str:
    if value.lower() in ("", NO_PRIORITY, "null"):
        return NO_PRIORITY
    return Priority(value.upper()).value


def _enum_or_blank(kind: type[StrEnum]) -> Callable[[str], str]:
    return lambda value: kind(value.lower()).value if value else ""


def _enum_list(kind: type[StrEnum]) -> Callable[[str], str]:
    def parse(value: str) -> str:
        parts = {kind(p.strip().lower()).value for p in value.split(";") if p.strip()}
        return ";".join(sorted(parts))

    return parse


def _yes_no(value: str) -> str:
    lowered = value.lower()
    if lowered in ("yes", "y", "true", "1"):
        return "yes"
    if lowered in ("", "no", "n", "false", "0"):
        return "no"
    raise ValueError("use yes or no")


_NORMALIZE: dict[str, Callable[[str], str]] = {
    "priority": _priority,
    "message_type": _enum_or_blank(MessageType),
    "vulnerable": _enum_list(Vulnerability),
    "suspicion_reasons": _enum_list(SuspicionReason),
    "water_level": _enum_or_blank(WaterLevel),
    "status_update_kind": _enum_or_blank(StatusUpdateKind),
    "medical_emergency": _yes_no,
    "is_suspicious": _yes_no,
    "location_resolvable": _yes_no,
    "people_count": lambda value: str(int(value)) if value else "",
}


# --- agreement


def cohens_kappa(a: Sequence[str], b: Sequence[str], order: Sequence[str] | None = None) -> float:
    """Cohen's kappa. With `order`, linearly weighted: near misses count partly."""
    if len(a) != len(b) or not a:
        raise ValueError("need two equal, non-empty answer lists")
    categories = list(order) if order else sorted(set(a) | set(b))
    index = {c: i for i, c in enumerate(categories)}
    k = len(categories)

    def weight(i: int, j: int) -> float:
        if order is None or k == 1:
            return 1.0 if i == j else 0.0
        return 1.0 - abs(i - j) / (k - 1)

    n = len(a)
    count_a, count_b = Counter(a), Counter(b)
    observed = sum(weight(index[x], index[y]) for x, y in zip(a, b, strict=True)) / n
    expected = sum(
        weight(index[x], index[y]) * count_a[x] * count_b[y] / (n * n)
        for x in categories
        for y in categories
    )
    return 1.0 if expected == 1.0 else (observed - expected) / (1.0 - expected)


PRIORITY_ORDER = [p.value for p in Priority] + [NO_PRIORITY]


@dataclass(frozen=True)
class Agreement:
    labeled: int
    priority_kappa: float
    priority_weighted_kappa: float
    message_type_kappa: float
    percent: dict[str, float]
    disagreements: list[tuple[str, str, str, str]]  # id, field, a, b


def agreement(a: dict[str, Answer], b: dict[str, Answer]) -> Agreement:
    """Compare messages both labelers answered (a non-empty message type)."""
    ids = [i for i in a if i in b and a[i].fields["message_type"] and b[i].fields["message_type"]]
    if not ids:
        raise SheetError("no message is labeled in both sheets")

    def column(answers: dict[str, Answer], field: str) -> list[str]:
        return [answers[i].fields[field] for i in ids]

    percent = {
        field: sum(x == y for x, y in zip(column(a, field), column(b, field), strict=True))
        / len(ids)
        for field in COMPARED
    }
    disagreements = [
        (i, field, a[i].fields[field], b[i].fields[field])
        for i in ids
        for field in COMPARED
        if a[i].fields[field] != b[i].fields[field]
    ]
    return Agreement(
        labeled=len(ids),
        priority_kappa=cohens_kappa(column(a, "priority"), column(b, "priority")),
        priority_weighted_kappa=cohens_kappa(
            column(a, "priority"), column(b, "priority"), PRIORITY_ORDER
        ),
        message_type_kappa=cohens_kappa(column(a, "message_type"), column(b, "message_type")),
        percent=percent,
        disagreements=disagreements,
    )


def write_disagreements(found: Agreement, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "field", "labeler_a", "labeler_b", "final", "why"])
        for message_id, field, value_a, value_b in found.disagreements:
            writer.writerow([message_id, field, value_a, value_b, "", ""])


def agreement_report(found: Agreement) -> str:
    lines = [
        f"Messages labeled by both: {found.labeled}",
        f"Priority kappa: {found.priority_kappa:.2f} "
        f"(linearly weighted: {found.priority_weighted_kappa:.2f}; target 0.70)",
        f"Message type kappa: {found.message_type_kappa:.2f}",
        "Percent agreement:",
        *(f"  {field}: {value:.0%}" for field, value in found.percent.items()),
        f"Disagreements to adjudicate: {len(found.disagreements)}",
    ]
    return "\n".join(lines)


# --- apply


@dataclass(frozen=True)
class Resolution:
    final: str
    why: str


def read_resolutions(path: Path | None) -> dict[tuple[str, str], Resolution]:
    if path is None:
        return {}
    with path.open(encoding="utf-8-sig", newline="") as file:
        return {
            (row["id"].strip(), row["field"].strip()): Resolution(
                normalize(row["field"].strip(), row["final"], row["id"])
                if row["final"].strip()
                else "",
                row["why"].strip(),
            )
            for row in csv.DictReader(file)
        }


def _higher_priority(x: str, y: str) -> str:
    return min(x, y, key=PRIORITY_ORDER.index)


def final_answers(
    message_id: str, a: Answer, b: Answer, resolutions: dict[tuple[str, str], Resolution]
) -> tuple[dict[str, str], list[str]]:
    """The agreed value per field, and notes on how each disagreement was settled."""
    final: dict[str, str] = {}
    notes: list[str] = []
    for field in COMPARED:
        if a.fields[field] == b.fields[field]:
            final[field] = a.fields[field]
            continue
        resolved = resolutions.get((message_id, field))
        if resolved and resolved.final:
            final[field] = resolved.final
            notes.append(f"{field}: {resolved.why or 'adjudicated'}")
        elif field == "priority":
            # Rubric tie-breaker: when still unsure, the higher priority wins.
            final[field] = _higher_priority(a.fields[field], b.fields[field])
            notes.append("priority: still split, higher priority kept (rubric tie-breaker)")
        else:
            raise SheetError(
                f"{message_id}: {field} is unresolved ({a.fields[field]} vs {b.fields[field]})"
            )
    return final, notes


def to_labels(final: dict[str, str]) -> Labels:
    def split(value: str) -> list[str]:
        return [v for v in value.split(";") if v]

    return Labels(
        priority=None if final["priority"] == NO_PRIORITY else Priority(final["priority"]),
        people_count=int(final["people_count"]) if final["people_count"] else None,
        vulnerable=[Vulnerability(v) for v in split(final["vulnerable"])],
        water_level=WaterLevel(final["water_level"] or "unknown"),
        medical_emergency=final["medical_emergency"] == "yes",
        status_update_kind=StatusUpdateKind(final["status_update_kind"])
        if final["status_update_kind"]
        else None,
        is_suspicious=final["is_suspicious"] == "yes",
        suspicion_reasons=[SuspicionReason(r) for r in split(final["suspicion_reasons"])],
    )


def truth_mismatches(
    message: DatasetMessage, final: dict[str, str], by_id: dict[str, DatasetMessage]
) -> list[str]:
    """Where the labelers read the message differently from the generator's truth."""
    truth = message.truth
    found = []
    if final["message_type"] and final["message_type"] != truth.message_type.value:
        found.append(
            f"message_type: labelers {final['message_type']}, truth {truth.message_type.value}"
        )
    resolvable = "yes" if truth.location_resolvable else "no"
    if final["location_resolvable"] != resolvable:
        found.append(
            f"location_resolvable: labelers {final['location_resolvable']}, truth {resolvable}"
        )
    linked = by_id.get(final["same_household_as"]) if final["same_household_as"] else None
    if linked is not None and linked.truth.household_id != truth.household_id:
        found.append(
            f"same_household_as {linked.id}: truth says {linked.truth.household_id} "
            f"vs {truth.household_id}"
        )
    return found


@dataclass(frozen=True)
class Applied:
    written: int
    adjudicated: int
    label_problems: list[str]
    generator_errors: list[str]


def apply_labels(
    messages_path: Path,
    a: dict[str, Answer],
    b: dict[str, Answer],
    resolutions: dict[tuple[str, str], Resolution],
) -> Applied:
    """Rewrite only the labeled lines; every other line stays byte for byte."""
    problems: list[str] = []
    messages = load_jsonl(messages_path, DatasetMessage, problems)
    if problems:
        raise SheetError(f"messages.jsonl is invalid: {problems[0]}")
    by_id = {m.id: m for m in messages}
    lines = messages_path.read_text(encoding="utf-8").splitlines()

    written = adjudicated = 0
    problems_found: list[str] = []
    generator_errors: list[str] = []
    for number, line in enumerate(lines):
        if not line.strip():
            continue
        message = by_id[json.loads(line)["id"]]
        answer_a, answer_b = a.get(message.id), b.get(message.id)
        if not (
            answer_a
            and answer_b
            and answer_a.fields["message_type"]
            and answer_b.fields["message_type"]
        ):
            continue
        final, notes = final_answers(message.id, answer_a, answer_b, resolutions)
        labels = to_labels(final)
        problems_found += [
            f"{message.id}: {p}" for p in label_problems(message.truth.message_type, labels)
        ]
        generator_errors += [f"{message.id}: {e}" for e in truth_mismatches(message, final, by_id)]
        split_notes = [n for n in (answer_a.notes, answer_b.notes) if n]
        meta = LabelMeta(
            status="adjudicated" if notes else "labeled",
            labeler_a={**answer_a.fields, "notes": answer_a.notes},
            labeler_b={**answer_b.fields, "notes": answer_b.notes},
            rubric_version=RUBRIC_VERSION,
            notes="; ".join(notes + split_notes),
        )
        updated = message.model_copy(update={"labels": labels, "label_meta": meta})
        lines[number] = json.dumps(updated.model_dump(mode="json"), ensure_ascii=False)
        written += 1
        adjudicated += bool(notes)

    messages_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return Applied(written, adjudicated, problems_found, generator_errors)


# --- CLI


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = parser.add_subparsers(dest="command", required=True)

    export = commands.add_parser("export", help="write a blank labeling sheet")
    export.add_argument("--split", choices=["dev", "eval", "calibration"], default="dev")
    export.add_argument("--out", type=Path, required=True)

    agree = commands.add_parser("agree", help="compare two filled sheets")
    agree.add_argument("sheet_a", type=Path)
    agree.add_argument("sheet_b", type=Path)
    agree.add_argument("--out", type=Path, required=True, help="disagreements sheet to write")

    apply = commands.add_parser("apply", help="write agreed and adjudicated labels")
    apply.add_argument("sheet_a", type=Path)
    apply.add_argument("sheet_b", type=Path)
    apply.add_argument("--resolved", type=Path, help="the adjudicated disagreements sheet")
    apply.add_argument("--messages", type=Path, default=MESSAGES)

    args = parser.parse_args(argv)
    try:
        if args.command == "export":
            problems: list[str] = []
            messages = load_jsonl(MESSAGES, DatasetMessage, problems)
            count = export_sheet(messages, args.split, args.out)
            print(f"Wrote {count} {args.split} messages to {args.out}")
        elif args.command == "agree":
            found = agreement(read_sheet(args.sheet_a), read_sheet(args.sheet_b))
            write_disagreements(found, args.out)
            print(agreement_report(found))
            print(f"Wrote {args.out}: fill in `final` and `why`, then run apply.")
        else:
            applied = apply_labels(
                args.messages,
                read_sheet(args.sheet_a),
                read_sheet(args.sheet_b),
                read_resolutions(args.resolved),
            )
            print(
                f"Wrote labels for {applied.written} messages ({applied.adjudicated} adjudicated)."
            )
            for line in applied.label_problems:
                print(f"label problem: {line}", file=sys.stderr)
            for line in applied.generator_errors:
                print(f"possible generator error (truth.* not changed): {line}")
            if applied.label_problems:
                print(
                    "Fix the label problems above in the sheets and apply again.", file=sys.stderr
                )
                return 1
    except SheetError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
