"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import type { Map as MapLibreMap, Marker, Popup } from "maplibre-gl";
import { useEffect, useRef } from "react";

import { Text } from "@/components/ui";
import type { CaseView } from "@/lib/api/types";
import { PRIORITY_LABEL } from "@/lib/format";

const MARIKINA: [number, number] = [121.1, 14.65];
// Copied from the installed package by scripts/copy-map-worker.mjs.
const WORKER_URL = "/maplibre-gl-worker.mjs";
const FLOOD_MAP_URL = "/assets/hazard/marikina-flood-100yr.geojson";
const FLOOD_ATTRIBUTION = "Flood hazard: Project NOAH (ODbL)";

// OpenFreeMap: OpenStreetMap vector tiles with 3D buildings, no API key. The style
// carries its own OpenStreetMap attribution.
const STYLE_URL = "https://tiles.openfreemap.org/styles/liberty";
// Terrain Tiles on AWS Open Data: elevation, so the river valley reads in 3D.
const TERRAIN_TILES = "https://elevation-tiles-prod.s3.amazonaws.com/terrarium/{z}/{x}/{y}.png";
const TERRAIN_ATTRIBUTION = "Terrain: Terrain Tiles on AWS";
// Marikina is a shallow valley: exaggerate it so the slope toward the river shows.
const TERRAIN_EXAGGERATION = 2.5;
const VIEW = { pitch: 55, bearing: -20 };

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
  // Under the buildings, so the flood reads as water at street level.
  map.addLayer(
    {
      id: "flood",
      type: "fill",
      source: "flood",
      paint: {
        "fill-opacity": 0.45,
        "fill-color": [
          "match",
          ["get", "level"],
          3,
          token("high"),
          2,
          token("medium"),
          token("low"),
        ],
      },
    },
    map.getLayer("building") ? "building" : undefined,
  );
}

/** Elevation under the whole map, with hillshade so slopes read without tilting. */
function addTerrain(map: MapLibreMap) {
  map.addSource("terrain", {
    type: "raster-dem",
    tiles: [TERRAIN_TILES],
    encoding: "terrarium",
    tileSize: 256,
    maxzoom: 15,
    attribution: TERRAIN_ATTRIBUTION,
  });
  map.addLayer(
    {
      id: "hillshade",
      type: "hillshade",
      source: "terrain",
      paint: { "hillshade-exaggeration": 0.3 },
    },
    map.getLayer("building") ? "building" : undefined,
  );
  map.setTerrain({ source: "terrain", exaggeration: TERRAIN_EXAGGERATION });
}

/** Every located open case as a pin; the selected one is larger and centred. */
export function CaseMap({ cases, selectedId, onSelect }: CaseMapProps) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<MapLibreMap | null>(null);
  // Pins are kept between refreshes, so their size transition and ping can run.
  const pins = useRef(new Map<string, Pin>());
  const markerClass = useRef<typeof Marker | null>(null);
  const popupClass = useRef<typeof Popup | null>(null);
  // One card, on the selected pin: what the case is, without leaving the map.
  const popup = useRef<Popup | null>(null);
  const centredOn = useRef<string | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;
    const current = pins.current;
    // maplibre-gl touches `window` on import, so load it only in the browser.
    void import("maplibre-gl").then((maplibregl) => {
      if (cancelled || !container.current) return;
      maplibregl.setWorkerUrl(WORKER_URL);
      markerClass.current = maplibregl.Marker;
      popupClass.current = maplibregl.Popup;
      const created = new maplibregl.Map({
        container: container.current,
        style: STYLE_URL,
        center: MARIKINA,
        zoom: 13.5,
        ...VIEW,
        maxPitch: 70,
        // Four sources to credit: compact keeps the legend clear on a small panel.
        attributionControl: { compact: true },
      });
      // Tilt and rotate with right-drag or two fingers; the compass resets the view.
      created.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
      created.on("load", () => {
        addTerrain(created);
        addFloodLayer(created);
      });
      map.current = created;
    });
    return () => {
      cancelled = true;
      popup.current = null;
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
    const chosen = located.find((item) => item.case_id === selectedId);
    const PopupClass = popupClass.current;
    if (!chosen) {
      popup.current?.remove();
    } else if (PopupClass) {
      popup.current ??= new PopupClass({
        className: "sk-map-card",
        closeButton: false,
        closeOnClick: false,
        maxWidth: "none",
        // Above the selected pin, which is 32px across.
        offset: 20,
      });
      popup.current
        .setLngLat([chosen.location.lng!, chosen.location.lat!])
        .setDOMContent(cardContent(chosen));
      if (!popup.current.isOpen()) popup.current.addTo(map.current);
    }
    // Re-centre only when the selection changes, not on every refresh.
    if (chosen && centredOn.current !== chosen.case_id) {
      // Not `essential`, so MapLibre jumps instead of flying under reduced motion.
      map.current.flyTo({
        center: [chosen.location.lng!, chosen.location.lat!],
        zoom: 16,
        ...VIEW,
      });
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

/** The selected case at a glance. Built as DOM: MapLibre renders it outside React. */
function cardContent(item: CaseView) {
  const card = document.createElement("div");
  card.dataset.testid = "map-card";
  card.className = "sk-map-card-body";
  const line = (className: string, text: string) => {
    const element = document.createElement("p");
    element.className = className;
    element.textContent = text;
    card.append(element);
  };
  const facts = [
    item.location.barangay ?? "Location pending",
    item.people_count != null ? `${item.people_count} people` : undefined,
    item.assigned_team ?? (item.status === "open" ? "Unassigned" : item.status),
  ].filter(Boolean);
  line("sk-map-card-priority", item.priority ? PRIORITY_LABEL[item.priority] : "No priority");
  card.lastElementChild!.setAttribute("data-priority", item.priority ?? "none");
  line("sk-map-card-summary", item.english_summary ?? "No summary yet");
  line("sk-map-card-meta", facts.join(" · "));
  if (item.reason) line("sk-map-card-meta", `Why: ${item.reason}`);
  return card;
}
