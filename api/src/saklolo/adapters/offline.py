"""Stand-ins for paid services, so the demo runs from a fresh clone without AWS.

Recorded calls are served by the call-cache decorators; these answer the misses. A
missed model call raises, and DispatchService keeps that message for a human.
"""

from typing import NoReturn

from pydantic import BaseModel

from saklolo.adapters.call_cache import JsonlCache
from saklolo.domain.errors import ServiceUnavailableError
from saklolo.domain.models import Location
from saklolo.domain.ports import ModelCall


class UnrecordedModel:
    def generate[OutputT: BaseModel](
        self, system_prompt: str, prompt: str, output_type: type[OutputT]
    ) -> ModelCall[OutputT]:
        _unrecorded()


class UnrecordedEmbedder:
    def embed(self, text: str) -> list[float]:
        _unrecorded()


class NoGeocoder:
    """Offline, only barangays named in the text resolve; others get the ask-back."""

    def geocode(self, query: str) -> Location | None:
        return None


class CopyingCache(JsonlCache):
    """Reads from `source` and keeps a copy of each hit, to record a smaller cache."""

    def __init__(self, source: JsonlCache, path_cache: JsonlCache) -> None:
        self._source = source
        self._target = path_cache

    def get(self, key: str) -> object | None:
        value = self._source.get(key)
        if value is not None and self._target.get(key) is None:
            self._target.put(key, value)
        return value


def _unrecorded() -> NoReturn:
    raise ServiceUnavailableError("offline demo: this call was not recorded")
