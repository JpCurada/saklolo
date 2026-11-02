from datetime import UTC, datetime, timedelta

from saklolo.domain.cases import Case, DedupePolicy, cosine_similarity, find_matching_case
from saklolo.domain.models import UNKNOWN_LOCATION, Location

POLICY = DedupePolicy(similarity_threshold=0.8, window=timedelta(hours=12), radius_km=1.5)
NOW = datetime(2026, 11, 10, 12, tzinfo=UTC)
MALANDAY = Location(barangay="Malanday", lat=14.663, lng=121.100)
FORTUNE = Location(barangay="Fortune", lat=14.665, lng=121.126)


def case(case_id: str, sender: str, location: Location, hours_ago: float = 1) -> Case:
    seen = NOW - timedelta(hours=hours_ago)
    return Case(case_id, {sender}, location, [1.0, 0.0], seen, seen)


def test_senders_own_open_case_matches_regardless_of_text() -> None:
    cases = [case("a", "+639000000001", MALANDAY)]

    match = find_matching_case(cases, "+639000000001", [0.0, 1.0], MALANDAY, NOW, POLICY)

    assert match is not None and match.same_sender


def test_a_sender_in_another_barangay_is_a_different_household() -> None:
    cases = [case("a", "+639000000001", MALANDAY)]

    match = find_matching_case(cases, "+639000000001", [1.0, 0.0], FORTUNE, NOW, POLICY)

    assert match is None  # even with identical text: a volunteer may report both


def test_similar_nearby_case_matches() -> None:
    cases = [case("a", "+639000000001", MALANDAY)]

    match = find_matching_case(cases, "+639000000002", [0.9, 0.1], MALANDAY, NOW, POLICY)

    assert match is not None and match.case.case_id == "a"


def test_similar_case_far_away_does_not_match() -> None:
    cases = [case("a", "+639000000001", MALANDAY)]

    assert find_matching_case(cases, "+639000000002", [1.0, 0.0], FORTUNE, NOW, POLICY) is None


def test_case_outside_the_time_window_does_not_match() -> None:
    cases = [case("a", "+639000000001", MALANDAY, hours_ago=20)]

    assert find_matching_case(cases, "+639000000001", [1.0, 0.0], MALANDAY, NOW, POLICY) is None


def test_unknown_location_can_still_match_by_similarity() -> None:
    cases = [case("a", "+639000000001", MALANDAY)]

    match = find_matching_case(cases, "+639000000002", [1.0, 0.0], UNKNOWN_LOCATION, NOW, POLICY)

    assert match is not None


def test_missing_embedding_never_matches_and_never_crashes() -> None:
    assert cosine_similarity([], [1.0, 0.0]) == 0.0
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0, 0.0]) == 0.0
