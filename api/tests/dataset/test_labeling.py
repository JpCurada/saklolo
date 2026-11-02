"""The human labeling kit: export, agreement, and adjudicated labels."""

import csv
import json
import shutil
from pathlib import Path

import pytest

from saklolo.config import REPO_ROOT
from saklolo.dataset.io import load_jsonl
from saklolo.dataset.labeling import (
    CONTEXT_COLUMNS,
    LABEL_COLUMNS,
    SheetError,
    agreement,
    apply_labels,
    cohens_kappa,
    export_sheet,
    read_resolutions,
    read_sheet,
)
from saklolo.dataset.schema import DatasetMessage
from saklolo.domain.models import Priority, Vulnerability

MESSAGES = REPO_ROOT / "data" / "messages.jsonl"


def dev_messages() -> list[DatasetMessage]:
    problems: list[str] = []
    return load_jsonl(MESSAGES, DatasetMessage, problems)


def write_sheet(path: Path, rows: list[dict[str, str]]) -> Path:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CONTEXT_COLUMNS + LABEL_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in writer.fieldnames})
    return path


def answer(message_id: str, **fields: str) -> dict[str, str]:
    base = {
        "id": message_id,
        "priority": "P1",
        "message_type": "rescue",
        "people_count": "5",
        "vulnerable": "infant",
        "water_level": "roof",
        "medical_emergency": "no",
        "is_suspicious": "no",
        "location_resolvable": "yes",
    }
    return base | fields


# --- export


def test_the_sheet_shows_the_message_but_never_the_answers(tmp_path: Path) -> None:
    out = tmp_path / "sheet.csv"

    count = export_sheet(dev_messages(), "dev", out)

    content = out.read_text(encoding="utf-8")
    with out.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert count == len(rows) == 150
    assert list(rows[0]) == CONTEXT_COLUMNS + LABEL_COLUMNS
    assert all(rows[0][column] == "" for column in LABEL_COLUMNS)
    assert "generator_intent" not in content
    assert "hh-0" not in content  # no household ids from truth.*
    assert "recycled_from" not in content


# --- agreement


def test_kappa_matches_a_worked_example() -> None:
    # 10 items, 7 agreements; expected chance agreement 0.5 -> kappa 0.4.
    a = ["yes"] * 5 + ["no"] * 5
    b = ["yes"] * 4 + ["no"] + ["yes"] * 2 + ["no"] * 3

    assert cohens_kappa(a, b) == pytest.approx(0.4)


def test_weighted_kappa_counts_a_near_miss_partly() -> None:
    order = ["P1", "P2", "P3", "P4"]
    a = ["P1", "P2", "P3", "P4"]
    near = ["P2", "P2", "P3", "P4"]
    far = ["P4", "P2", "P3", "P4"]

    assert cohens_kappa(a, near, order) > cohens_kappa(a, far, order)


def test_agreement_reports_kappa_and_every_disagreement(tmp_path: Path) -> None:
    a = write_sheet(tmp_path / "a.csv", [answer("msg-0001"), answer("msg-0002", priority="P2")])
    b = write_sheet(
        tmp_path / "b.csv",
        [
            answer("msg-0001"),
            answer("msg-0002", priority="P3"),
            answer("msg-0003", message_type=""),
        ],
    )

    found = agreement(read_sheet(a), read_sheet(b))

    assert found.labeled == 2  # msg-0003 is unlabeled in b
    assert found.percent["priority"] == 0.5
    assert found.percent["water_level"] == 1.0
    assert found.disagreements == [("msg-0002", "priority", "P2", "P3")]


def test_a_bad_cell_names_the_message_and_column(tmp_path: Path) -> None:
    sheet = write_sheet(tmp_path / "a.csv", [answer("msg-0001", priority="P9")])

    with pytest.raises(SheetError, match="msg-0001: priority='P9'"):
        read_sheet(sheet)


# --- apply


@pytest.fixture
def messages_copy(tmp_path: Path) -> Path:
    return Path(shutil.copy(MESSAGES, tmp_path / "messages.jsonl"))


def first_rescue() -> DatasetMessage:
    return next(m for m in dev_messages() if m.truth.message_type.value == "rescue")


def test_agreed_and_adjudicated_answers_become_labels(tmp_path: Path, messages_copy: Path) -> None:
    target = first_rescue()
    sheet_a = write_sheet(tmp_path / "a.csv", [answer(target.id, water_level="neck")])
    sheet_b = write_sheet(tmp_path / "b.csv", [answer(target.id, water_level="roof")])
    resolved = tmp_path / "resolved.csv"
    resolved.write_text(
        "id,field,labeler_a,labeler_b,final,why\n"
        f"{target.id},water_level,neck,roof,roof,says nasa bubong\n",
        encoding="utf-8",
    )

    applied = apply_labels(
        messages_copy, read_sheet(sheet_a), read_sheet(sheet_b), read_resolutions(resolved)
    )

    updated = next(m for m in load_jsonl(messages_copy, DatasetMessage, []) if m.id == target.id)
    assert applied.written == 1 and applied.adjudicated == 1
    assert updated.labels is not None
    assert updated.labels.priority == Priority.CRITICAL
    assert updated.labels.vulnerable == [Vulnerability.INFANT]
    assert updated.labels.water_level.value == "roof"
    assert updated.label_meta.status == "adjudicated"
    assert updated.label_meta.labeler_a is not None
    assert updated.label_meta.labeler_a["water_level"] == "neck"
    assert "says nasa bubong" in updated.label_meta.notes


def test_a_split_priority_keeps_the_higher_one(tmp_path: Path, messages_copy: Path) -> None:
    target = first_rescue()
    sheet_a = write_sheet(tmp_path / "a.csv", [answer(target.id, priority="P2")])
    sheet_b = write_sheet(tmp_path / "b.csv", [answer(target.id, priority="P1")])

    apply_labels(messages_copy, read_sheet(sheet_a), read_sheet(sheet_b), {})

    updated = next(m for m in load_jsonl(messages_copy, DatasetMessage, []) if m.id == target.id)
    assert updated.labels is not None and updated.labels.priority == Priority.CRITICAL
    assert "higher priority kept" in updated.label_meta.notes


def test_other_unresolved_fields_must_be_adjudicated(tmp_path: Path, messages_copy: Path) -> None:
    target = first_rescue()
    sheet_a = write_sheet(tmp_path / "a.csv", [answer(target.id, people_count="4")])
    sheet_b = write_sheet(tmp_path / "b.csv", [answer(target.id, people_count="5")])

    with pytest.raises(SheetError, match="people_count is unresolved"):
        apply_labels(messages_copy, read_sheet(sheet_a), read_sheet(sheet_b), {})


def test_disagreeing_with_truth_is_reported_not_fixed(tmp_path: Path, messages_copy: Path) -> None:
    target = first_rescue()
    rows = [answer(target.id, message_type="relief_info", priority="P4")]
    sheet = write_sheet(tmp_path / "a.csv", rows)

    applied = apply_labels(messages_copy, read_sheet(sheet), read_sheet(sheet), {})

    assert applied.generator_errors == [
        f"{target.id}: message_type: labelers relief_info, truth rescue"
    ]
    updated = next(m for m in load_jsonl(messages_copy, DatasetMessage, []) if m.id == target.id)
    assert updated.truth.message_type.value == "rescue"


def test_unlabeled_lines_stay_byte_for_byte(tmp_path: Path, messages_copy: Path) -> None:
    target = first_rescue()
    sheet = write_sheet(tmp_path / "a.csv", [answer(target.id)])
    before = MESSAGES.read_text(encoding="utf-8").splitlines()

    apply_labels(messages_copy, read_sheet(sheet), read_sheet(sheet), {})

    after = messages_copy.read_text(encoding="utf-8").splitlines()
    changed = [i for i, (x, y) in enumerate(zip(before, after, strict=True)) if x != y]
    assert len(changed) == 1
    assert json.loads(after[changed[0]])["id"] == target.id
