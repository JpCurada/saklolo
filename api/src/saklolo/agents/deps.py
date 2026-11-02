"""Everything the pipeline needs from outside, injected by a composition root."""

from dataclasses import dataclass, field

from saklolo.agents.prompts import PromptSet
from saklolo.domain.cases import DedupePolicy
from saklolo.domain.ports import (
    CaseStore,
    Embedder,
    Escalation,
    FloodHazardMap,
    Geocoder,
    PostArchive,
    StructuredModel,
)


@dataclass(frozen=True)
class PipelineDeps:
    model: StructuredModel
    geocoder: Geocoder
    embedder: Embedder
    cases: CaseStore
    dedupe: DedupePolicy
    escalation_threshold: float
    prompts: PromptSet = field(default_factory=PromptSet.default)
    # Shown in the agent trace next to steps that called the model.
    model_id: str = ""
    # Low-confidence triage gets a Swarm review; None sends it straight to a human.
    escalation: Escalation | None = None
    escalation_model_id: str = ""
    # Known past-typhoon posts, for spotting recycled ones; None skips that check.
    archive: PostArchive | None = None
    # Project NOAH's flood map: context for the dispatcher, never a flag.
    flood_map: FloodHazardMap | None = None
