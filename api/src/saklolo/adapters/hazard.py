"""FloodHazardMap over a GeoJSON extract of Project NOAH's flood map (data/hazard/)."""

import json
from pathlib import Path
from typing import Any

Ring = list[list[float]]


def _inside(lng: float, lat: float, ring: Ring) -> bool:
    """Ray casting: odd crossings mean inside."""
    inside = False
    x0, y0 = ring[-1]
    for x1, y1 in ring:
        if (y0 > lat) != (y1 > lat) and lng < x0 + (lat - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
        x0, y0 = x1, y1
    return inside


def _in_polygon(lng: float, lat: float, rings: list[Ring]) -> bool:
    return _inside(lng, lat, rings[0]) and not any(_inside(lng, lat, hole) for hole in rings[1:])


class GeoJsonFloodMap:
    def __init__(self, path: Path) -> None:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        self._levels: list[tuple[int, list[list[Ring]]]] = []
        for feature in data["features"]:
            geometry = feature["geometry"]
            coordinates = geometry["coordinates"]
            polygons = [coordinates] if geometry["type"] == "Polygon" else coordinates
            self._levels.append((feature["properties"]["level"], polygons))
        self._levels.sort(key=lambda item: item[0], reverse=True)
        points = [p for _, polygons in self._levels for rings in polygons for p in rings[0]]
        self._west = min(p[0] for p in points)
        self._east = max(p[0] for p in points)
        self._south = min(p[1] for p in points)
        self._north = max(p[1] for p in points)

    def level_at(self, lat: float, lng: float) -> int | None:
        if not (self._west <= lng <= self._east and self._south <= lat <= self._north):
            return None
        for level, polygons in self._levels:
            if any(_in_polygon(lng, lat, rings) for rings in polygons):
                return level
        return 0
