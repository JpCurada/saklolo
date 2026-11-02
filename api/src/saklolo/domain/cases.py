"""Cases and the rule for whether a new message belongs to an open one (ADR 0003)."""

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from saklolo.domain.models import Location


@dataclass
class Case:
    case_id: str
    senders: set[str]
    location: Location
    embedding: list[float]
    opened_at: datetime
    last_seen: datetime
    closed: bool = False  # only a dispatcher closes a case
    reported_safe: bool = False  # resident says they're safe; awaiting dispatcher confirmation
    message_count: int = 1

    @property
    def awaiting_location(self) -> bool:
        return self.location.barangay is None


@dataclass(frozen=True)
class DedupePolicy:
    similarity_threshold: float
    window: timedelta
    radius_km: float


@dataclass(frozen=True)
class CaseMatch:
    case: Case
    similarity: float
    same_sender: bool = field(default=False)


def find_matching_case(
    open_cases: list[Case],
    sender: str,
    embedding: list[float],
    location: Location,
    now: datetime,
    policy: DedupePolicy,
) -> CaseMatch | None:
    """Best open case for a message: the sender's own case, else the most similar nearby one.

    A sender's own case must be in the same barangay: a volunteer reporting a second
    household elsewhere gets a second case. An extra case is cheap; a household merged
    out of the queue is not.
    """
    recent = [c for c in open_cases if not c.closed and now - c.last_seen <= policy.window]
    own = [c for c in recent if sender in c.senders and same_barangay(c.location, location)]
    if own:
        return CaseMatch(max(own, key=lambda c: c.last_seen), similarity=1.0, same_sender=True)

    nearby = [
        c
        for c in recent
        if sender not in c.senders and is_nearby(c.location, location, policy.radius_km)
    ]
    scored = [CaseMatch(c, cosine_similarity(c.embedding, embedding)) for c in nearby]
    best = max(scored, key=lambda m: m.similarity, default=None)
    if best is None or best.similarity < policy.similarity_threshold:
        return None
    return best


def same_barangay(a: Location, b: Location) -> bool:
    """Unknown locations can't rule a case out: an update rarely repeats the place."""
    return a.barangay is None or b.barangay is None or a.barangay == b.barangay


def is_nearby(a: Location, b: Location, radius_km: float) -> bool:
    """Unknown locations can't rule a case out, so they count as nearby."""
    if a.barangay is None or b.barangay is None:
        return True
    if a.barangay == b.barangay:
        return True
    if a.lat is None or a.lng is None or b.lat is None or b.lng is None:
        return False
    return distance_km((a.lat, a.lng), (b.lat, b.lng)) <= radius_km


def distance_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Haversine distance between two (lat, lng) points."""
    earth_radius_km = 6371.0
    phi1, phi2 = math.radians(a[0]), math.radians(b[0])
    d_phi = phi2 - phi1
    d_lambda = math.radians(b[1] - a[1])
    h = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * earth_radius_km * math.asin(math.sqrt(h))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """0.0 when either vector is missing (embedder outage) or they can't be compared."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norms = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norms if norms else 0.0
