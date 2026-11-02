"""Core data shapes. Labels, prompts, and the API all use these."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Priority(StrEnum):
    CRITICAL = "P1"
    HIGH = "P2"
    MODERATE = "P3"
    INFO = "P4"


class WaterLevel(StrEnum):
    ROOF = "roof"
    NECK = "neck"
    CHEST = "chest"
    WAIST = "waist"
    KNEE = "knee"
    UNKNOWN = "unknown"


class Vulnerability(StrEnum):
    INFANT = "infant"
    SENIOR = "senior"
    PERSON_WITH_DISABILITY = "pwd"
    PREGNANT = "pregnant"
    INJURED = "injured"


class VerificationStatus(StrEnum):
    UNVERIFIED = "unverified"
    CORROBORATED = "corroborated"
    CONFIRMED_BY_REPLY = "confirmed_by_reply"
    CONFIRMED_BY_BARANGAY = "confirmed_by_barangay"
    SUSPICIOUS = "suspicious"


class MessageType(StrEnum):
    RESCUE = "rescue"
    STATUS_UPDATE = "status_update"
    DUPLICATE = "duplicate"
    RELIEF_INFO = "relief_info"
    VAGUE_LOCATION = "vague_location"
    RECYCLED = "recycled"
    SPAM = "spam"


class StatusUpdateKind(StrEnum):
    RESCUED = "rescued"
    WORSENING = "worsening"
    IMPROVING = "improving"
    OTHER = "other"


class SuspicionReason(StrEnum):
    RECYCLED = "recycled"
    IMPLAUSIBLE_LOCATION = "implausible_location"
    SPAM_PATTERN = "spam_pattern"
    SENDER_PATTERN = "sender_pattern"


class Channel(StrEnum):
    SMS = "sms"
    MESSENGER = "messenger"
    TELEGRAM = "telegram"
    WEB = "web"


class LocationSource(StrEnum):
    TEXT = "text"  # the message names the barangay
    GEOCODER = "geocoder"  # Amazon Location resolved the place words
    REPLY = "reply"  # the resident answered the ask-back question
    # The reviewers' lookup of a landmark, still waiting for the resident's answer.
    REVIEWER = "reviewer"
    UNKNOWN = "unknown"


class Location(BaseModel):
    model_config = ConfigDict(frozen=True)

    barangay: str | None
    lat: float | None = None
    lng: float | None = None
    source: LocationSource = LocationSource.UNKNOWN


UNKNOWN_LOCATION = Location(barangay=None)


class InboundMessage(BaseModel):
    """What every channel adapter sends to intake."""

    sender: str
    text: str
    channel: Channel
    received_at: datetime


class OutboundMessage(BaseModel):
    """A text sent to a resident (through the Notifier port)."""

    recipient: str
    body: str
    sent_at: datetime


class ExtractedRequest(BaseModel):
    """Structured output of the extract node."""

    is_rescue_request: bool
    is_status_update: bool
    status_update_kind: StatusUpdateKind | None = None
    people_count: int | None = Field(default=None, ge=0)
    vulnerable: list[Vulnerability] = Field(default_factory=list)
    water_level: WaterLevel = WaterLevel.UNKNOWN
    medical_emergency: bool = False
    location_text: str | None = None
    barangay: str | None = Field(default=None, description="Marikina barangay named in the text")
    english_summary: str
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("vulnerable", mode="before")
    @classmethod
    def _null_means_none_listed(cls, value: object) -> object:
        # Some models send null for "nobody vulnerable"; rejecting it causes retry loops.
        return [] if value is None else value

    @field_validator("water_level", mode="before")
    @classmethod
    def _null_means_unknown(cls, value: object) -> object:
        return WaterLevel.UNKNOWN if value is None else value


class TriageDecision(BaseModel):
    """Structured output of the triage node and the escalation Swarm."""

    priority: Priority
    reason: str = Field(max_length=200)
    confidence: float = Field(ge=0.0, le=1.0)

    def needs_escalation(self, threshold: float) -> bool:
        return self.confidence < threshold


class TraceStatus(StrEnum):
    RAN = "ran"
    SKIPPED = "skipped"


class TraceStep(BaseModel):
    """One Graph step's work on one message, shown to the dispatcher."""

    step: str
    status: TraceStatus
    duration_ms: int
    detail: str
    # The model or AWS service the step called, if any.
    service: str | None = None


class TriageOutcome(BaseModel):
    """What the pipeline hands to the dispatch queue for one message."""

    priority: Priority | None = Field(description="None when the message closes a case or is spam")
    is_suspicious: bool
    suspicion_reasons: list[SuspicionReason] = Field(default_factory=list)
    case_id: str | None = Field(description="None for messages that aren't about a household")
    location: Location
    ask_back_question: str | None = Field(description="Set when the location must be asked")
    english_summary: str | None
    people_count: int | None = None
    vulnerable: list[Vulnerability] = Field(default_factory=list)
    water_level: WaterLevel = WaterLevel.UNKNOWN
    medical_emergency: bool = False
    reports_safe: bool = False
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)
    needs_escalation: bool
