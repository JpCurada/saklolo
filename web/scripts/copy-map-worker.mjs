// MapLibre 6 ships its web worker as a separate file; serve the installed version from public/.
import { copyFileSync } from "node:fs";

copyFileSync(
  "node_modules/maplibre-gl/dist/maplibre-gl-worker.mjs",
  "public/maplibre-gl-worker.mjs",
);
