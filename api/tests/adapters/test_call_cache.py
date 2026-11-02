from pathlib import Path

from saklolo.adapters.call_cache import CachingEmbedder, CachingStructuredModel, JsonlCache
from saklolo.domain.models import Priority, TriageDecision
from tests.agents.fakes import FakeEmbedder, FakeStructuredModel

DECISION = TriageDecision(priority=Priority.HIGH, reason="Trapped, water steady", confidence=0.8)


def test_repeated_model_call_is_served_from_disk_even_after_restart(tmp_path: Path) -> None:
    inner = FakeStructuredModel({TriageDecision: DECISION})
    path = tmp_path / "calls.jsonl"

    first = CachingStructuredModel(inner, JsonlCache(path), "model-a")
    first.generate("system", "prompt", TriageDecision)
    restarted = CachingStructuredModel(inner, JsonlCache(path), "model-a")
    call = restarted.generate("system", "prompt", TriageDecision)

    assert len(inner.calls) == 1
    assert call.output == DECISION
    assert call.usage.input_tokens == 100  # original usage, so cost metrics stay comparable


def test_different_model_or_prompt_is_a_cache_miss(tmp_path: Path) -> None:
    inner = FakeStructuredModel({TriageDecision: DECISION})
    cache = JsonlCache(tmp_path / "calls.jsonl")

    CachingStructuredModel(inner, cache, "model-a").generate("system", "prompt", TriageDecision)
    CachingStructuredModel(inner, cache, "model-b").generate("system", "prompt", TriageDecision)
    CachingStructuredModel(inner, cache, "model-a").generate("system v2", "prompt", TriageDecision)

    assert len(inner.calls) == 3


def test_embeddings_are_cached(tmp_path: Path) -> None:
    texts: list[str] = []

    def embed(text: str) -> list[float]:
        texts.append(text)
        return [0.5, 0.5]

    embedder = CachingEmbedder(FakeEmbedder(embed), JsonlCache(tmp_path / "e.jsonl"), "titan")

    assert embedder.embed("a") == embedder.embed("a") == [0.5, 0.5]
    assert texts == ["a"]


def test_truncated_cache_line_is_skipped(tmp_path: Path) -> None:
    path = tmp_path / "calls.jsonl"
    path.write_text('{"key": "a", "value": 1}\n{"key": "b", "val', encoding="utf-8")

    cache = JsonlCache(path)

    assert cache.get("a") == 1
    assert cache.get("b") is None


def test_cached_output_that_no_longer_validates_is_fetched_again(tmp_path: Path) -> None:
    inner = FakeStructuredModel({TriageDecision: DECISION})
    cache = JsonlCache(tmp_path / "calls.jsonl")
    model = CachingStructuredModel(inner, cache, "model-a")
    model.generate("system", "prompt", TriageDecision)
    [key] = cache._entries  # corrupt the stored output as a stricter validator would see it
    cache._entries[key]["output"]["confidence"] = 7

    model.generate("system", "prompt", TriageDecision)

    assert len(inner.calls) == 2
