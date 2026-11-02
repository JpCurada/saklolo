"""Marikina's barangays: official (PSGC) names, spellings people use, and rough centers."""

import re
import unicodedata
from itertools import pairwise

MARIKINA_BARANGAYS = (
    "Barangka",
    "Calumpang",
    "Concepcion Uno",
    "Concepcion Dos",
    "Fortune",
    "Industrial Valley Complex",
    "Jesus de la Peña",
    "Malanday",
    "Marikina Heights",
    "Nangka",
    "Parang",
    "San Roque",
    "Santa Elena",
    "Santo Niño",
    "Tañong",
    "Tumana",
)

# Approximate barangay centers (lat, lng). Good enough to filter nearby cases;
# replace with PSGC/boundary centroids before claiming street-level accuracy.
BARANGAY_CENTERS: dict[str, tuple[float, float]] = {
    "Barangka": (14.6290, 121.0820),
    "Calumpang": (14.6230, 121.0870),
    "Concepcion Uno": (14.6470, 121.1060),
    "Concepcion Dos": (14.6420, 121.1190),
    "Fortune": (14.6650, 121.1260),
    "Industrial Valley Complex": (14.6230, 121.0960),
    "Jesus de la Peña": (14.6300, 121.0880),
    "Malanday": (14.6630, 121.1000),
    "Marikina Heights": (14.6500, 121.1180),
    "Nangka": (14.6710, 121.1080),
    "Parang": (14.6600, 121.1100),
    "San Roque": (14.6290, 121.0990),
    "Santa Elena": (14.6330, 121.0980),
    "Santo Niño": (14.6380, 121.0960),
    "Tañong": (14.6340, 121.0920),
    "Tumana": (14.6560, 121.0960),
}

# (min_lat, min_lng, max_lat, max_lng) around Marikina City.
MARIKINA_BOUNDS = (14.60, 121.07, 14.70, 121.14)


def fold(text: str) -> str:
    """Lowercase, drop accents and dots: 'Sto. Niño' and 'sto nino' compare equal."""
    decomposed = unicodedata.normalize("NFKD", text.lower().replace(".", ""))
    return " ".join("".join(c for c in decomposed if not unicodedata.combining(c)).split())


_SHORT_FORMS = {
    "sto nino": "Santo Niño",
    "sta elena": "Santa Elena",
    "jdp": "Jesus de la Peña",
    "jesus dela pena": "Jesus de la Peña",
    "ivc": "Industrial Valley Complex",
}

# Every folded spelling people write, mapped to the official name.
BARANGAY_SPELLINGS: dict[str, str] = {
    fold(name): name for name in MARIKINA_BARANGAYS
} | _SHORT_FORMS

# "Parang" is also everyday Filipino ("it seems"); only count it after a place word.
_AMBIGUOUS = {"parang"}
_PLACE_WORD = r"(?:brgy|barangay|taga|sa)\s+"
_MENTION = re.compile(
    "|".join(
        rf"(?:{_PLACE_WORD})?\b{re.escape(spelling)}\b"
        if spelling not in _AMBIGUOUS
        else rf"\b{_PLACE_WORD}{re.escape(spelling)}\b"
        for spelling in sorted(BARANGAY_SPELLINGS, key=len, reverse=True)
    )
)


def canonical_barangay(name: str | None) -> str | None:
    """The official name for a barangay a model or person wrote, or None if unknown."""
    return BARANGAY_SPELLINGS.get(fold(name)) if name else None


def find_barangay(text: str) -> str | None:
    """The first barangay mentioned anywhere in free text, or None."""
    match = _MENTION.search(fold(text))
    if match is None:
        return None
    spelling = re.sub(_PLACE_WORD, "", match.group(0), count=1).strip()
    return BARANGAY_SPELLINGS.get(spelling)


def _words(text: str) -> frozenset[str]:
    return frozenset(text.split())


_FILLER_WORDS = _words(
    "tapat ng sa may malapit likod yung ung ang po kami sila dito diyan banda harap tabi "
    "kanto na at near the of behind beside across in on"
)
# Landmarks that exist on every street: geocoding them returns a random branch.
_GENERIC_LANDMARKS = _words(
    "7-11 7-eleven 711 simbahan kapilya chapel church covered court school eskwelahan "
    "palengke market talipapa bakery botika pharmacy tindahan store sari-sari waiting shed "
    "gate asul blue bahay house compound apartment ilog river tulay bridge sm mall "
    "subdivision barangay brgy hall elementary"
)
# A word after these is a person's name ("tindahan ni Aling Cora"), never a place.
_BEFORE_A_NAME = _words("ni aling mang kuya ate tito tita lola lolo")


def distinctive_words(place_words: str) -> list[str]:
    """Words that can identify a specific place ("tumana" in "Tumana Bridge")."""
    words = re.findall(r"[a-z0-9-]+", fold(place_words))
    names = {after for before, after in pairwise(words) if before in _BEFORE_A_NAME}
    ignored = _FILLER_WORDS | _GENERIC_LANDMARKS | _BEFORE_A_NAME | names
    return [w for w in words if w not in ignored and len(w) >= 3]


def in_marikina(lat: float, lng: float) -> bool:
    min_lat, min_lng, max_lat, max_lng = MARIKINA_BOUNDS
    return min_lat <= lat <= max_lat and min_lng <= lng <= max_lng
