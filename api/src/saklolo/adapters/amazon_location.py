"""Geocoder implemented with Amazon Location Service (Places API v2, geo-places)."""

from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from saklolo.domain.errors import ServiceUnavailableError
from saklolo.domain.models import Location, LocationSource
from saklolo.domain.places import canonical_barangay, distinctive_words, fold, in_marikina

MARIKINA_CENTER_LNG_LAT = [121.10, 14.65]
# Address fields that can hold a barangay name, most specific first.
BARANGAY_FIELDS = ("SubDistrict", "District", "Locality")


class AmazonLocationGeocoder:
    def __init__(self, geo_places: Any) -> None:
        self._client = geo_places

    def geocode(self, query: str) -> Location | None:
        try:
            response = self._client.geocode(
                QueryText=f"{query}, Marikina City",
                BiasPosition=MARIKINA_CENTER_LNG_LAT,
                Filter={"IncludeCountries": ["PHL"]},
                MaxResults=1,
            )
        except (BotoCoreError, ClientError) as error:
            raise ServiceUnavailableError(f"Amazon Location geocode failed: {error}") from error
        items = response.get("ResultItems", [])
        return _to_location(items[0], query) if items else None


def _to_location(item: dict[str, Any], query: str) -> Location | None:
    """Accept only Marikina results that name a known barangay and match the query."""
    position = item.get("Position")
    if not position or len(position) != 2:
        return None  # unexpected response shape: treat as "couldn't place it"
    lng, lat = position
    address = item.get("Address", {})
    barangay = next((b for f in BARANGAY_FIELDS if (b := canonical_barangay(address.get(f)))), None)
    if barangay is None or not in_marikina(lat, lng):
        return None
    found = fold(f"{item.get('Title', '')} {address.get('Label', '')}")
    if not any(word in found for word in distinctive_words(query)):
        return None  # the geocoder fell back to something unrelated
    return Location(barangay=barangay, lat=lat, lng=lng, source=LocationSource.GEOCODER)
