from datetime import UTC, datetime

from saklolo.adapters.geocode_cache import CachedGeocoder
from saklolo.adapters.memory import InMemoryCaseStore
from saklolo.agents.ask_back import apply_reply
from saklolo.agents.nodes.geolocate import resolve_location
from saklolo.domain.cases import Case
from saklolo.domain.errors import ServiceUnavailableError
from saklolo.domain.models import UNKNOWN_LOCATION, Location, LocationSource
from tests.agents.fakes import FakeGeocoder

TUMANA_BRIDGE = Location(
    barangay="Tumana", lat=14.6566, lng=121.0956, source=LocationSource.GEOCODER
)


def test_named_barangay_wins_without_geocoding() -> None:
    geocoder = FakeGeocoder()

    location = resolve_location("Malanday", "likod ng kapilya", "...", geocoder)

    assert location.barangay == "Malanday"
    assert location.source == LocationSource.TEXT
    assert geocoder.queries == []


def test_text_search_finds_a_barangay_the_model_missed() -> None:
    location = resolve_location(None, None, "help po sto nino purok 1", FakeGeocoder())

    assert location.barangay == "Santo Niño"


def test_geocoder_places_landmarks_when_no_barangay_is_named() -> None:
    geocoder = FakeGeocoder({"Tumana Bridge": TUMANA_BRIDGE})

    location = resolve_location(None, "Tumana Bridge", "malapit sa bridge", geocoder)

    assert location == TUMANA_BRIDGE


def test_geocoder_outage_leaves_the_location_unknown() -> None:
    class DownGeocoder:
        def geocode(self, query: str) -> Location | None:
            raise ServiceUnavailableError("down")

    assert (
        resolve_location(None, "tapat ng 7-11", "tapat ng 7-11", DownGeocoder()) == UNKNOWN_LOCATION
    )


def test_cached_geocoder_asks_once_per_place_including_misses() -> None:
    inner = FakeGeocoder({"Tumana Bridge": TUMANA_BRIDGE})
    cached = CachedGeocoder(inner, {})

    for query in ["Tumana Bridge", "tumana bridge", "tapat ng 7-11", "tapat ng 7-11"]:
        cached.geocode(query)

    assert inner.queries == ["Tumana Bridge", "tapat ng 7-11"]


def test_reply_resolves_a_case_waiting_for_its_location() -> None:
    cases = InMemoryCaseStore()
    now = datetime.now(UTC)
    cases.save(Case("case-0001", {"+639000000001"}, UNKNOWN_LOCATION, [1.0], now, now))

    location = apply_reply("case-0001", "Malanday po, tapat ng 7-Eleven", cases, FakeGeocoder())

    assert location.barangay == "Malanday"
    assert location.source == LocationSource.REPLY


def test_generic_landmarks_are_not_geocoded() -> None:
    geocoder = FakeGeocoder()

    location = resolve_location(None, "tapat ng 7-11 yung may asul na gate", "...", geocoder)

    assert location == UNKNOWN_LOCATION
    assert geocoder.queries == []


def test_peoples_names_are_not_geocoded() -> None:
    geocoder = FakeGeocoder()

    resolve_location(None, "kanto ng tindahan ni Aling Cora", "...", geocoder)

    assert geocoder.queries == []
