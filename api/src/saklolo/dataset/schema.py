"""Row schemas for data/*.jsonl (docs/dataset-spec.md §3)."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from saklolo.domain.models import (
    Channel,
    MessageType,
    Priority,
    StatusUpdateKind,
    SuspicionReason,
    Vulnerability,
    WaterLevel,
)

FAKE_PHONE_PATTERN = r"^\+639000000\d{3}$"

Split = Literal["dev", "eval", "calibration"]


class _Row(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Household(_Row):
    household_id: str = Field(pattern=r"^hh-\d{4}$")
    barangay: str
    street_or_landmark: str
    lat: float = Field(ge=14.60, le=14.70)
    lng: float = Field(ge=121.07, le=121.14)
    members: int = Field(ge=1)
    vulnerable: list[Vulnerability]
    contact_names: list[str]
    senders: list[str] = Field(min_length=1)


class Labels(_Row):
    """Subjective fields. Same shape for human labels and generator intent."""

    priority: Priority | None
    people_count: int | None = Field(default=None, ge=0)
    vulnerable: list[Vulnerability] = Field(default_factory=list)
    water_level: WaterLevel = WaterLevel.UNKNOWN
    medical_emergency: bool = False
    status_update_kind: StatusUpdateKind | None = None
    is_suspicious: bool = False
    suspicion_reasons: list[SuspicionReason] = Field(default_factory=list)


class Truth(_Row):
    message_type: MessageType
    household_id: str | None
    recycled_from: str | None
    location_resolvable: bool


class LabelMeta(_Row):
    status: Literal["pending", "labeled", "adjudicated"]
    labeler_a: dict[str, object] | None = None
    labeler_b: dict[str, object] | None = None
    rubric_version: str
    notes: str = ""


class DatasetMessage(_Row):
    id: str = Field(pattern=r"^msg-\d{4}$")
    split: Split
    scenario_hour: float = Field(ge=0, le=36)
    channel: Channel
    sender: str = Field(pattern=FAKE_PHONE_PATTERN)
    text: str = Field(min_length=1)
    ask_back_reply: str | None
    truth: Truth
    labels: Labels | None
    label_meta: LabelMeta
    generator_intent: Labels


class ArchivePost(_Row):
    archive_id: str = Field(pattern=r"^arc-\d{4}$")
    event: str
    posted: date
    text: str
