# Marikina flood hazard

`marikina-flood-100yr.geojson` is Project NOAH's 100-year flood hazard map for Metro
Manila, clipped to Marikina and simplified to about 13 m.

**Source:** Project NOAH downloadable products, `Flood/100yr/Metro Manila.zip`, through
the [bettergovph mirror](https://huggingface.co/datasets/bettergovph/project-noah-hazard-maps).
Flood models by PAGASA.

**License:** this extract is an adapted database under the
[Open Data Commons Open Database License 1.0](https://opendatacommons.org/licenses/odbl/1.0/),
not the repo's Apache-2.0 license. Credit "Project NOAH and its contributors" wherever
it is used or shown.

`level` is 1 low (0 to 0.5 m), 2 medium (0.5 to 1.5 m), 3 high (over 1.5 m).

**Why it's context, not a flag:** Saklolo's locations are barangay centers, not houses.
Within 500 m of every center there is a high-hazard area, so "this place doesn't flood"
can't be concluded at that precision. A plausibility flag would hit real emergencies in
upland barangays near creeks. It needs house-level locations first.

To rebuild, unzip the source and run `build_extract.py` as its docstring says, then copy
the result to `web/public/assets/hazard/`.
