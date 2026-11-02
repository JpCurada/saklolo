"""Resume a case paused on "Anong barangay at kalye o purok po kayo?".

The resident's reply is short ("Malanday po, tapat ng 7-Eleven"), so it is
placed with the same deterministic search and cached geocoder as geolocate,
with no model call. Triage already ran when the first message arrived.
"""

from saklolo.agents.nodes.geolocate import resolve_location
from saklolo.agents.nodes.normalize import clean, mask_phones
from saklolo.domain.models import Location, LocationSource
from saklolo.domain.ports import CaseStore, Geocoder


def apply_reply(case_id: str, reply: str, cases: CaseStore, geocoder: Geocoder) -> Location:
    """Update the case's location from the reply; returns the case's location afterwards."""
    case = cases.get(case_id)
    if case is None:
        raise KeyError(f"unknown case {case_id}")
    if not case.awaiting_location or case.closed:
        return case.location  # nothing to resume: don't pay for a geocode
    text = mask_phones(clean(reply))
    location = resolve_location(None, text, text, geocoder)
    if location.barangay is not None:
        case.location = location.model_copy(update={"source": LocationSource.REPLY})
        cases.save(case)
    return case.location
