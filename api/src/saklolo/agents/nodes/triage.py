"""Set the priority. Rules handle the clear cases; the model handles the rest."""

from saklolo.agents.nodes.extract import message_block
from saklolo.agents.state import PipelineState
from saklolo.domain.models import ExtractedRequest, Priority, StatusUpdateKind, TriageDecision
from saklolo.domain.ports import StructuredModel


def triage(state: PipelineState, model: StructuredModel, system_prompt: str) -> None:
    extraction = state.extraction
    if extraction is None:
        raise ValueError("triage needs the extract node's output")
    reports_safe = extraction.status_update_kind == StatusUpdateKind.RESCUED
    if reports_safe and not extraction.is_rescue_request:
        state.verdict_reason = "Sender reports they are safe"
        return
    if not (extraction.is_rescue_request or extraction.is_status_update):
        state.decision = TriageDecision(
            priority=Priority.INFO,
            reason="Not a rescue request",
            confidence=extraction.confidence,
        )
        return

    call = model.generate(system_prompt, _prompt(state, extraction), TriageDecision)
    state.decision = call.output
    state.usage.append(call.usage)


def _prompt(state: PipelineState, extraction: ExtractedRequest) -> str:
    facts = extraction.model_dump_json(exclude={"confidence"})
    return f"{message_block(state.model_text)}\n<facts>\n{facts}\n</facts>"
