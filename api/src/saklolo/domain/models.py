"""Core data shapes. Labels, prompts, and the API all use these (docs/triage-rubric.md)."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


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


class InboundMessage(BaseModel):
    """What every channel adapter sends to intake (ADR 0001)."""

    sender: str
    text: str
    channel: str
    received_at: datetime


class ExtractedRequest(BaseModel):
    """Structured output of the extract node."""

    is_rescue_request: bool
    is_status_update: bool
    people_count: int | None = Field(default=None, ge=0)
    vulnerable: list[Vulnerability] = Field(default_factory=list)
    water_level: WaterLevel = WaterLevel.UNKNOWN
    medical_emergency: bool = False
    location_text: str | None = None
    english_summary: str
    confidence: float = Field(ge=0.0, le=1.0)


class TriageDecision(BaseModel):
    """Structured output of the triage node and the escalation Swarm."""

    priority: Priority
    reason: str = Field(max_length=200)
    confidence: float = Field(ge=0.0, le=1.0)

    def needs_escalation(self, threshold: float) -> bool:
        return self.confidence < threshold
