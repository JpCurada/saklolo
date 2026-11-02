"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import type { Map as MapLibreMap, Marker } from "maplibre-gl";
import { useEffect, useRef } from "react";

import { Text } from "@/components/ui";
import type { CaseView } from "@/lib/api/types";

const MARIKINA: [number, number] = [121.1, 14.65];
// Copied from the installed package by scripts/copy-map-worker.mjs.
const WORKER_URL = "/maplibre-gl-worker.mjs";
const FLOOD_MAP_URL = "/assets/hazard/marikina-flood-100yr.geojson";
const FLOOD_ATTRIBUTION = "Flood hazard: Project NOAH (ODbL)";

// OpenStreetMap raster tiles: no API key; attribution is required and shown.
const STYLE = {
  version: 8 as const,
  sources: {
    osm: {
      type: "raster" as const,
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors",
    },
  },
  layers: [{ id: "osm", type: "raster" as const, source: "osm" }],
};

interface Pin {
  marker: Marker;
  element: HTMLButtonElement;
}

interface CaseMapProps {
  cases: CaseView[];
  selectedId: string | undefined;
  onSelect: (caseId: string) => void;
}

/** Project NOAH's 100-year flood hazard, under the pins. MapLibre can't read CSS variables. */
function addFloodLayer(map: MapLibreMap) {
  const token = (name: string) =>
    getComputedStyle(document.documentElement).getPropertyValue(`--sk-color-map-hazard-${name}`);
  map.addSource("flood", { type: "geojson", data: FLOOD_MAP_URL, attribution: FLOOD_ATTRIBUTION });
  map.addLayer({
    id: "flood",
    type: "fill",
    source: "flood",
    paint: {
      "fill-opacity": 0.45,
      "fill-color": ["match", ["get", "level"], 3, token("high"), 2, token("medium"), token("low")],
    },
  });
}

/** Every located open case as a pin; the selected one is larger and centred. */
export function CaseMap({ cases, selectedId, onSelect }: CaseMapProps) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<MapLibreMap | null>(null);
  // Pins are kept between refreshes, so their size transition and ping can run.
  const pins = useRef(new Map<string, Pin>());
  const markerClass = useRef<typeof Marker | null>(null);
  const centredOn = useRef<string | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;
    const current = pins.current;
    // maplibre-gl touches `window` on import, so load it only in the browser.
    void import("maplibre-gl").then((maplibregl) => {
      if (cancelled || !container.current) return;
      maplibregl.setWorkerUrl(WORKER_URL);
      markerClass.current = maplibregl.Marker;
      const created = new maplibregl.Map({
        container: container.current,
        style: STYLE,
        center: MARIKINA,
        zoom: 13,
      });
      created.on("load", () => addFloodLayer(created));
      map.current = created;
    });
    return () => {
      cancelled = true;
      map.current?.remove();
      map.current = null;
      current.clear();
    };
  }, []);

  useEffect(() => {
    const MarkerClass = markerClass.current;
    if (!map.current || !MarkerClass) return;
    const located = cases.filter((item) => item.location.lat != null && item.location.lng != null);
    const stillShown = new Set(located.map((item) => item.case_id));
    for (const [caseId, pin] of pins.current) {
      if (stillShown.has(caseId)) continue;
      pin.marker.remove();
      pins.current.delete(caseId);
    }
    for (const item of located) {
      const lngLat: [number, number] = [item.location.lng!, item.location.lat!];
      let pin = pins.current.get(item.case_id);
      if (!pin) {
        const element = pinElement(item.case_id, onSelect);
        const marker = new MarkerClass({ element }).setLngLat(lngLat).addTo(map.current);
        pin = { marker, element };
        pins.current.set(item.case_id, pin);
      }
      pin.marker.setLngLat(lngLat);
      paintPin(pin.element, item, item.case_id === selectedId);
    }
    // Re-centre only when the selection changes, not on every refresh.
    const chosen = located.find((item) => item.case_id === selectedId);
    if (chosen && centredOn.current !== chosen.case_id) {
      // Not `essential`, so MapLibre jumps instead of flying under reduced motion.
      map.current.flyTo({ center: [chosen.location.lng!, chosen.location.lat!], zoom: 15 });
      centredOn.current = chosen.case_id;
    }
  });

  return (
    <div className="relative h-full w-full">
      <div ref={container} data-testid="case-map" className="h-full w-full" />
      <dl data-testid="flood-legend" className="sk-map-legend">
        <dt>
          <Text variant="caption-bold">Flood hazard</Text>
        </dt>
        {(["low", "medium", "high"] as const).map((level) => (
          <dd key={level} className="flex items-center gap-1">
            <span aria-hidden className={`sk-map-swatch sk-map-swatch-${level}`} />
            <Text variant="caption" tone="muted">
              {level}
            </Text>
          </dd>
        ))}
      </dl>
    </div>
  );
}

function pinElement(caseId: string, onSelect: (caseId: string) => void) {
  const element = document.createElement("button");
  element.type = "button";
  element.className = "sk-pin";
  element.dataset.caseId = caseId;
  const ring = document.createElement("span");
  ring.className = "sk-ping sk-pin-ring";
  const label = document.createElement("span");
  label.className = "sk-pin-label";
  element.append(ring, label);
  element.addEventListener("click", () => onSelect(caseId));
  return element;
}

/** Updates a pin in place. The label means color is never the only signal. */
function paintPin(element: HTMLButtonElement, item: CaseView, selected: boolean) {
  const [ring, label] = element.children as HTMLCollectionOf<HTMLElement>;
  element.dataset.testid = selected ? "map-pin" : "map-dot";
  element.dataset.priority = item.priority ?? "none";
  element.dataset.selected = String(selected);
  element.setAttribute("aria-label", `Case ${item.case_id}, ${item.priority ?? "no priority"}`);
  element.setAttribute("aria-pressed", String(selected));
  label.textContent = item.priority ?? "?";
  ring.hidden = !(item.priority === "P1" && item.status === "open" && !item.assigned_team);
}
