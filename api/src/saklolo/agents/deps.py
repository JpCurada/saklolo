"""Everything the pipeline needs from outside, injected by a composition root."""

from dataclasses import dataclass, field

from saklolo.agents.prompts import PromptSet
from saklolo.domain.cases import DedupePolicy
from saklolo.domain.ports import CaseStore, Embedder, Geocoder, StructuredModel


@dataclass(frozen=True)
class PipelineDeps:
    model: StructuredModel
    geocoder: Geocoder
    embedder: Embedder
    cases: CaseStore
    dedupe: DedupePolicy
    escalation_threshold: float
    prompts: PromptSet = field(default_factory=PromptSet.default)
