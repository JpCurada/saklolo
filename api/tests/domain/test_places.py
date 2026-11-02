import pytest

from saklolo.domain.places import canonical_barangay, find_barangay


@pytest.mark.parametrize(
    ("written", "official"),
    [
        ("Tanong", "Tañong"),
        ("sto. nino", "Santo Niño"),
        ("  JESUS DE LA PENA ", "Jesus de la Peña"),
        ("Malanday", "Malanday"),
    ],
)
def test_spellings_map_to_the_official_name(written: str, official: str) -> None:
    assert canonical_barangay(written) == official


@pytest.mark.parametrize("written", [None, "", "Provident Village", "Quezon City"])
def test_unknown_places_become_none(written: str | None) -> None:
    assert canonical_barangay(written) is None


@pytest.mark.parametrize(
    ("text", "barangay"),
    [
        ("HELP PO tumana purok 4 malapit tumana bridge", "Tumana"),
        ("JDP po kami malapit sa daan papuntang barangka", "Jesus de la Peña"),
        ("brgy parang po kami, trapped sa 2nd floor", "Parang"),
        ("taga parang po kami 2 tao", "Parang"),
        ("parang ulysses na naman, nasa bubong na kami", None),
        ("dito sa amin malapit sa ilog", None),
    ],
)
def test_find_barangay_in_free_text(text: str, barangay: str | None) -> None:
    assert find_barangay(text) == barangay
