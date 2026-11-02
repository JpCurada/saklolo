"""Turn the message into structured facts with one model call."""

from saklolo.agents.state import PipelineState
from saklolo.domain.models import ExtractedRequest
from saklolo.domain.places import canonical_barangay
from saklolo.domain.ports import StructuredModel


def message_block(text: str) -> str:
    """Resident text is untrusted: it only ever appears inside these tags."""
    return f"<message>\n{text}\n</message>"


def extract(state: PipelineState, model: StructuredModel, system_prompt: str) -> None:
    call = model.generate(system_prompt, message_block(state.model_text), ExtractedRequest)
    # Models drop accents or invent places; keep only official barangay names.
    barangay = canonical_barangay(call.output.barangay)
    state.extraction = call.output.model_copy(update={"barangay": barangay})
    state.usage.append(call.usage)
