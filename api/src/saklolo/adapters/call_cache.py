"""Disk caches for paid calls, so repeated experiments cost nothing.

Decorators over the StructuredModel and Embedder ports: the pipeline can't tell
whether a call was cached. A hit returns the original token usage, so cost
metrics stay comparable between cached and uncached runs.
"""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from saklolo.domain.ports import Embedder, ModelCall, ModelUsage, StructuredModel


class JsonlCache:
    """Append-only key → JSON value store in a single file."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries: dict[str, Any] = {}
        if path.exists():
            with path.open(encoding="utf-8") as file:
                for line in file:
                    self._load(line)

    def _load(self, line: str) -> None:
        try:
            entry = json.loads(line)
            self._entries[entry["key"]] = entry["value"]
        except (json.JSONDecodeError, KeyError, TypeError):
            pass  # a line cut short by a crash is just a miss

    def get(self, key: str) -> Any | None:
        return self._entries.get(key)

    def put(self, key: str, value: Any) -> None:
        self._entries[key] = value
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8", newline="\n") as file:
            file.write(json.dumps({"key": key, "value": value}, ensure_ascii=False) + "\n")


def cache_key(*parts: str) -> str:
    return hashlib.sha256(json.dumps(parts).encode("utf-8")).hexdigest()


class CachingStructuredModel:
    def __init__(self, inner: StructuredModel, cache: JsonlCache, model_id: str) -> None:
        self._inner = inner
        self._cache = cache
        self._model_id = model_id

    def generate[OutputT: BaseModel](
        self, system_prompt: str, prompt: str, output_type: type[OutputT]
    ) -> ModelCall[OutputT]:
        schema = json.dumps(output_type.model_json_schema(), sort_keys=True)
        key = cache_key(self._model_id, system_prompt, prompt, schema)
        if (hit := self._cached(key, output_type)) is not None:
            return hit
        call = self._inner.generate(system_prompt, prompt, output_type)
        self._cache.put(
            key, {"output": call.output.model_dump(mode="json"), "usage": asdict(call.usage)}
        )
        return call

    def _cached[OutputT: BaseModel](
        self, key: str, output_type: type[OutputT]
    ) -> ModelCall[OutputT] | None:
        hit = self._cache.get(key)
        if hit is None:
            return None
        try:  # validators can tighten without changing the schema: re-ask if it fails
            return ModelCall(output_type.model_validate(hit["output"]), ModelUsage(**hit["usage"]))
        except (ValidationError, KeyError, TypeError):
            return None


class CachingEmbedder:
    def __init__(self, inner: Embedder, cache: JsonlCache, model_key: str) -> None:
        """model_key must change whenever vectors change (model id and dimensions)."""
        self._inner = inner
        self._cache = cache
        self._model_key = model_key

    def embed(self, text: str) -> list[float]:
        key = cache_key(self._model_key, text)
        if (hit := self._cache.get(key)) is not None:
            return [float(x) for x in hit]
        vector = self._inner.embed(text)
        self._cache.put(key, vector)
        return vector
