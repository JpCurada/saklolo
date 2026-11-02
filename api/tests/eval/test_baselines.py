from saklolo.domain.models import Priority
from saklolo.eval.baselines import find_barangay, keyword_priority, normalize


def test_normalize_strips_accents_and_dots() -> None:
    assert normalize("Sto. Niño, Tañong") == "sto nino, tanong"


def test_roof_is_critical() -> None:
    assert keyword_priority(normalize("nasa bubong na kami")) == Priority.CRITICAL


def test_rescued_update_has_no_priority() -> None:
    assert keyword_priority(normalize("na rescue na po kami salamat")) is None


def test_message_without_keywords_is_info() -> None:
    assert keyword_priority(normalize("kailan babalik ang kuryente?")) == Priority.INFO


def test_barangay_alias_is_mapped_to_psgc_name() -> None:
    assert find_barangay(normalize("JDP po kami")) == "Jesus de la Peña"
