"""Clip Project NOAH's Metro Manila flood map to Marikina for the map layer and verify.

Run once, with the unzipped NOAH shapefile (data/hazard/README.md):
  uv run --no-project --with pyshp --with shapely python build_extract.py <shp> <out.geojson>
"""

import json
import sys

import shapefile
from shapely.geometry import LinearRing, Polygon, box, mapping
from shapely.ops import unary_union

# Marikina City with a margin (west, south, east, north).
MARIKINA = (121.07, 14.60, 121.14, 14.70)
SIMPLIFY_DEGREES = 0.00012  # about 13 m
MIN_AREA = 2e-8  # about 200 square meters
LEVELS = {1: "low", 2: "medium", 3: "high"}


def main(source: str, output: str) -> None:
    area = box(*MARIKINA)
    reader = shapefile.Reader(source)
    features = []
    for record in reader.iterShapeRecords():
        level = int(record.record["Var"])
        outer, holes = _rings_in_area(record.shape)
        print(level, len(outer), "rings in area", flush=True)
        clipped = unary_union(outer).difference(unary_union(holes)).intersection(area)
        parts = getattr(clipped, "geoms", [clipped])
        kept = [p for p in parts if p.geom_type == "Polygon" and p.area >= MIN_AREA]
        simple = unary_union(kept).simplify(SIMPLIFY_DEGREES, preserve_topology=True)
        geometry = json.loads(json.dumps(mapping(simple)))
        features.append(
            {
                "type": "Feature",
                "properties": {"level": level, "hazard": LEVELS[level]},
                "geometry": _rounded(geometry),
            }
        )
        print(level, simple.geom_type, f"{simple.area:.6f}", flush=True)
    collection = {
        "type": "FeatureCollection",
        "attribution": "Flood hazard: Project NOAH and its contributors, ODC-ODbL 1.0",
        "features": features,
    }
    with open(output, "w", encoding="utf-8") as file:
        json.dump(collection, file, separators=(",", ":"))


def _rings_in_area(polygon_shape):
    """Skip everything outside Marikina first: Metro Manila has over 100,000 rings."""
    west, south, east, north = MARIKINA
    points = polygon_shape.points
    starts = [*polygon_shape.parts, len(points)]
    outer, holes = [], []
    for start, end in zip(starts, starts[1:]):
        ring = points[start:end]
        xs = [point[0] for point in ring]
        ys = [point[1] for point in ring]
        if len(ring) < 4 or max(xs) < west or min(xs) > east or max(ys) < south or min(ys) > north:
            continue
        polygon = Polygon(ring).buffer(0)
        # Shapefiles wind outer rings clockwise and holes counterclockwise.
        (holes if LinearRing(ring).is_ccw else outer).append(polygon)
    return outer, holes


def _rounded(value):
    if isinstance(value, float):
        return round(value, 5)
    if isinstance(value, (list, tuple)):
        return [_rounded(item) for item in value]
    if isinstance(value, dict):
        return {key: _rounded(item) for key, item in value.items()}
    return value


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
