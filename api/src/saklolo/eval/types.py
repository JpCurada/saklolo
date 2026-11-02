"""What predictors see, what they return, and what they are scored against."""

from collections.abc import Sequence
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from saklolo.domain.models import Channel, MessageType, Priority


class EvalMessage(BaseModel):
    """The only view of a message a predictor gets. No truth, labels, or intent."""

    model_config = ConfigDict(frozen=True)

    id: str
    sender: str
    channel: Channel
    scenario_hour: float
    text: str
    # The resident's answer if the system asks "Anong kalye o purok po?" (dataset-spec §8).
    reply_if_asked: str | None


class Prediction(BaseModel):
    model_config = ConfigDict(frozen=True)

    message_id: str
    priority: Priority | None
    case_key: str | None = Field(description="Messages with the same key are one case")
    barangay: str | None
    is_suspicious: bool
    # True when the system asked the resident for their location (ask-back).
    asked_back: bool = False
    latency_s: float = Field(ge=0)
    cost_usd: float = Field(ge=0)
    # Set when the predictor failed on this message; it is then scored as a miss.
    error: str | None = None
    # Swarm escalation (graph predictor only). escalation_outcome is None when the
    # message never escalated; see agents.state.EscalationOutcome for the values.
    escalation_outcome: str | None = None
    escalation_agents: list[str] = Field(default_factory=list)
    first_priority: Priority | None = None
    first_confidence: float | None = None

    @property
    def escalated(self) -> bool:
        return self.escalation_outcome is not None


class GroundTruth(BaseModel):
    model_config = ConfigDict(frozen=True)

    message_id: str
    message_type: MessageType
    priority: Priority | None
    is_suspicious: bool
    household_id: str | None
    barangay: str | None


class Predictor(Protocol):
    name: str

    def predict(self, messages: Sequence[EvalMessage]) -> list[Prediction]:
        """Process messages in timeline order; may keep state across messages."""
        ...
