from saklolo.adapters.amazon_location import _to_location

TUMANA_ITEM = {
    "Title": "Tumana Bridge",
    "Position": [121.09563, 14.65663],
    "Address": {"Label": "Tumana Bridge, 1806 Marikina, Philippines", "District": "Tumana"},
}


def test_matching_result_inside_marikina_is_accepted() -> None:
    location = _to_location(TUMANA_ITEM, "Tumana Bridge")

    assert location is not None and location.barangay == "Tumana"


def test_result_that_does_not_mention_the_query_is_rejected() -> None:
    assert _to_location(TUMANA_ITEM, "kanto ng tindahan ni Aling Cora") is None


def test_result_outside_marikina_is_rejected() -> None:
    elsewhere = {**TUMANA_ITEM, "Position": [120.98, 14.55]}

    assert _to_location(elsewhere, "Tumana Bridge") is None
