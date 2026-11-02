"""Geocoder decorator that remembers answers, including "couldn't place it"."""

from collections.abc import MutableMapping

from saklolo.domain.models import Location
from saklolo.domain.places import fold
from saklolo.domain.ports import Geocoder


class CachedGeocoder:
    """The same landmark ("likod ng simbahan, Malanday") is geocoded once per run."""

    def __init__(self, inner: Geocoder, store: MutableMapping[str, Location | None]) -> None:
        self._inner = inner
        self._store = store

    def geocode(self, query: str) -> Location | None:
        key = fold(query)
        if key not in self._store:
            self._store[key] = self._inner.geocode(query)
        return self._store[key]
