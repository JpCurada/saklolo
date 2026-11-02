"""Per-message state shared by every Graph node through invocation_state."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from saklolo.domain.models import (
    UNKNOWN_LOCATION,
    ExtractedRequest,
    InboundMessage,
    Location,
    StatusUpdateKind,
    SuspicionReason,
    TriageDecision,
    TriageOutcome,
    WaterLevel,
)
from saklolo.domain.ports import ModelUsage

STATE_KEY = "saklolo_pipeline"

ASK_BACK_QUESTION = (
    "Salamat po. Anong barangay at kalye o purok po kayo? "
    "(What barangay and street or purok are you in?)"
)


class PrefilterVerdict(StrEnum):
    NEEDS_MODEL = "needs_model"
    SPAM = "spam"  # flagged and shown in the suspicious lane, never deleted


@dataclass
class PipelineState:
    message: InboundMessage
    clean_text: str = ""
    model_text: str = ""  # clean_text with phone numbers masked; the only text models see
    phones: list[str] = field(default_factory=list)
    verdict: PrefilterVerdict = PrefilterVerdict.NEEDS_MODEL
    verdict_reason: str = ""
    injection_suspected: bool = False  # flagged for the dispatcher; the model still reads it
    extraction: ExtractedRequest | None = None
    location: Location = UNKNOWN_LOCATION
    asks_location: bool = False
    case_id: str | None = None
    decision: TriageDecision | None = None
    usage: list[ModelUsage] = field(default_factory=list)

    def outcome(self, escalation_threshold: float) -> TriageOutcome:
        suspicious = self.verdict == PrefilterVerdict.SPAM or self.injection_suspected
        decision = self.decision
        extraction = self.extraction
        return TriageOutcome(
            priority=decision.priority if decision else None,
            is_suspicious=suspicious,
            suspicion_reasons=[SuspicionReason.SPAM_PATTERN] if suspicious else [],
            case_id=self.case_id,
            location=self.location,
            ask_back_question=ASK_BACK_QUESTION if self.asks_location else None,
            english_summary=extraction.english_summary if extraction else None,
            people_count=extraction.people_count if extraction else None,
            vulnerable=extraction.vulnerable if extraction else [],
            water_level=extraction.water_level if extraction else WaterLevel.UNKNOWN,
            medical_emergency=extraction.medical_emergency if extraction else False,
            reports_safe=bool(
                extraction and extraction.status_update_kind == StatusUpdateKind.RESCUED
            ),
            reason=decision.reason if decision else self.verdict_reason,
            confidence=decision.confidence if decision else 1.0,
            needs_escalation=decision.needs_escalation(escalation_threshold) if decision else False,
        )


def pipeline_state(invocation_state: dict[str, Any] | None) -> PipelineState:
    state = (invocation_state or {}).get(STATE_KEY)
    if not isinstance(state, PipelineState):
        raise TypeError(f"invocation_state[{STATE_KEY!r}] must hold a PipelineState")
    return state
