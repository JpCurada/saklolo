"""Load data/*.jsonl into typed rows."""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ValidationError

from saklolo.dataset.schema import ArchivePost, DatasetMessage, Household


@dataclass(frozen=True)
class Dataset:
    households: list[Household]
    messages: list[DatasetMessage]
    archive: list[ArchivePost]


def load_dataset(data_dir: Path) -> tuple[Dataset, list[str]]:
    """Parse every file; rows that fail the schema are skipped and reported."""
    problems: list[str] = []
    dataset = Dataset(
        households=load_jsonl(data_dir / "households.jsonl", Household, problems),
        messages=load_jsonl(data_dir / "messages.jsonl", DatasetMessage, problems),
        archive=load_jsonl(data_dir / "archive.jsonl", ArchivePost, problems),
    )
    return dataset, problems


def load_jsonl[RowT: BaseModel](
    path: Path, row_type: type[RowT], problems: list[str]
) -> list[RowT]:
    rows = []
    for number, line in _non_blank_lines(path):
        try:
            rows.append(row_type.model_validate_json(line))
        except ValidationError as error:
            problems.append(f"{path.name}:{number}: {error.errors()[0]['msg']}")
    return rows


def _non_blank_lines(path: Path) -> Iterable[tuple[int, str]]:
    with path.open(encoding="utf-8") as file:
        for number, line in enumerate(file, start=1):
            if line.strip():
                yield number, line
