"""The flood map against the real Marikina extract."""

from saklolo.adapters.hazard import GeoJsonFloodMap
from saklolo.config import REPO_ROOT
from saklolo.domain.places import BARANGAY_CENTERS

FLOOD_MAP = REPO_ROOT / "data" / "hazard" / "marikina-flood-100yr.geojson"


def test_riverside_barangays_are_high_hazard_and_upland_ones_are_not() -> None:
    flood_map = GeoJsonFloodMap(FLOOD_MAP)

    assert flood_map.level_at(*BARANGAY_CENTERS["Tumana"]) == 3
    assert flood_map.level_at(*BARANGAY_CENTERS["Malanday"]) == 3
    assert flood_map.level_at(*BARANGAY_CENTERS["Fortune"]) == 0


def test_a_point_outside_the_map_has_no_answer() -> None:
    assert GeoJsonFloodMap(FLOOD_MAP).level_at(14.5, 120.9) is None
