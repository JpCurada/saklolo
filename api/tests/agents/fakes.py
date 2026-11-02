"""Test doubles for the pipeline's ports."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import timedelta

from pydantic import BaseModel

from saklolo.adapters.memory import InMemoryCaseStore
from saklolo.agents.deps import PipelineDeps
from saklolo.domain.cases import DedupePolicy
from saklolo.domain.models import Location
from saklolo.domain.ports import ModelCall, ModelUsage

TEST_POLICY = DedupePolicy(similarity_threshold=0.8, window=timedelta(hours=12), radius_km=1.5)


@dataclass(frozen=True)
class RecordedCall:
    system_prompt: str
    prompt: str
    output_type: type[BaseModel]


@dataclass
class FakeStructuredModel:
    """Returns a canned output per output type and records every call."""

    outputs: dict[type[BaseModel], BaseModel]
    calls: list[RecordedCall] = field(default_factory=list)

    def generate[OutputT: BaseModel](
        self, system_prompt: str, prompt: str, output_type: type[OutputT]
    ) -> ModelCall[OutputT]:
        self.calls.append(RecordedCall(system_prompt, prompt, output_type))
        output = self.outputs[output_type]
        assert isinstance(output, output_type)
        return ModelCall(output=output, usage=ModelUsage(input_tokens=100, output_tokens=20))

    def called_with(self, output_type: type[BaseModel]) -> list[RecordedCall]:
        return [c for c in self.calls if c.output_type is output_type]


@dataclass
class FakeGeocoder:
    """Answers from a fixed table of place words; records every query."""

    places: dict[str, Location] = field(default_factory=dict)
    queries: list[str] = field(default_factory=list)

    def geocode(self, query: str) -> Location | None:
        self.queries.append(query)
        return self.places.get(query)


@dataclass
class FakeEmbedder:
    """Embeds with a caller-supplied function (default: every text is identical)."""

    embed_fn: Callable[[str], list[float]] = lambda _: [1.0, 0.0]

    def embed(self, text: str) -> list[float]:
        return self.embed_fn(text)


def fake_deps(
    model: FakeStructuredModel,
    geocoder: FakeGeocoder | None = None,
    embedder: FakeEmbedder | None = None,
    cases: InMemoryCaseStore | None = None,
) -> PipelineDeps:
    return PipelineDeps(
        model=model,
        geocoder=geocoder or FakeGeocoder(),
        embedder=embedder or FakeEmbedder(),
        cases=cases or InMemoryCaseStore(),
        dedupe=TEST_POLICY,
        escalation_threshold=0.75,
    )
