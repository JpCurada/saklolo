"""Place the message in a Marikina barangay, cheapest source first.

1. The barangay the extract node read from the message (already canonical)
2. A deterministic search of the whole text ("sto nino", "jdp", "brgy parang")
3. Amazon Location on the place words, through the cache
If none works for a rescue request, the resident is asked (ask-back); triage
still runs, so an urgent case is never held back by a missing location.
"""

import logging

from saklolo.agents.state import PipelineState
from saklolo.domain.errors import ServiceUnavailableError
from saklolo.domain.models import UNKNOWN_LOCATION, Location, LocationSource
from saklolo.domain.places import BARANGAY_CENTERS, distinctive_words, find_barangay
from saklolo.domain.ports import Geocoder

logger = logging.getLogger(__name__)


def geolocate(state: PipelineState, geocoder: Geocoder) -> None:
    extraction = state.extraction
    if extraction is None:
        raise ValueError("geolocate needs the extract node's output")
    about_a_household = extraction.is_rescue_request or extraction.is_status_update
    # Questions and relief requests get the free lookups only, never a paid geocode.
    place_words = extraction.location_text if about_a_household else None
    state.location = resolve_location(extraction.barangay, place_words, state.model_text, geocoder)
    state.asks_location = state.location.barangay is None and extraction.is_rescue_request


def resolve_location(
    named_barangay: str | None, place_words: str | None, full_text: str, geocoder: Geocoder
) -> Location:
    barangay = named_barangay or find_barangay(full_text)
    if barangay:
        lat, lng = BARANGAY_CENTERS[barangay]
        return Location(barangay=barangay, lat=lat, lng=lng, source=LocationSource.TEXT)
    if not place_words or not distinctive_words(place_words):
        # "tapat ng 7-11" matches some 7-Eleven somewhere: asking beats a wrong pin.
        return UNKNOWN_LOCATION
    try:
        return geocoder.geocode(place_words) or UNKNOWN_LOCATION
    except ServiceUnavailableError:
        logger.warning("geocoder unavailable; location left for ask-back")
        return UNKNOWN_LOCATION
