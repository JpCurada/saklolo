"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import type { Map as MapLibreMap, Marker } from "maplibre-gl";
import { useEffect, useRef } from "react";

import type { CaseView, Priority } from "@/lib/api/types";

const MARIKINA: [number, number] = [121.1, 14.65];
// Copied from the installed package by scripts/copy-map-worker.mjs.
const WORKER_URL = "/maplibre-gl-worker.mjs";
const PIN_COLOR: Record<Priority, string> = {
  P1: "#dc2626",
  P2: "#f97316",
  P3: "#fde047",
  P4: "#64748b",
};

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

interface CaseMapProps {
  cases: CaseView[];
  selectedId: string | undefined;
  onSelect: (caseId: string) => void;
}

/** Every located open case as a pin; the selected one is larger and centred. */
export function CaseMap({ cases, selectedId, onSelect }: CaseMapProps) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<MapLibreMap | null>(null);
  const markers = useRef<Marker[]>([]);
  const markerClass = useRef<typeof Marker | null>(null);
  const centredOn = useRef<string | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;
    // maplibre-gl touches `window` on import, so load it only in the browser.
    void import("maplibre-gl").then((maplibregl) => {
      if (cancelled || !container.current) return;
      maplibregl.setWorkerUrl(WORKER_URL);
      markerClass.current = maplibregl.Marker;
      map.current = new maplibregl.Map({
        container: container.current,
        style: STYLE,
        center: MARIKINA,
        zoom: 13,
      });
    });
    return () => {
      cancelled = true;
      map.current?.remove();
      map.current = null;
    };
  }, []);

  useEffect(() => {
    const MarkerClass = markerClass.current;
    if (!map.current || !MarkerClass) return;
    markers.current.forEach((marker) => marker.remove());
    markers.current = cases.flatMap((item) => {
      const { lat, lng } = item.location;
      if (lat == null || lng == null) return [];
      const selected = item.case_id === selectedId;
      const element = pinElement(item, selected, onSelect);
      return [new MarkerClass({ element }).setLngLat([lng, lat]).addTo(map.current!)];
    });
    // Re-centre only when the selection changes, not on every refresh.
    const chosen = cases.find((item) => item.case_id === selectedId);
    if (
      chosen &&
      centredOn.current !== chosen.case_id &&
      chosen.location.lat != null &&
      chosen.location.lng != null
    ) {
      map.current.easeTo({ center: [chosen.location.lng, chosen.location.lat], zoom: 15 });
      centredOn.current = chosen.case_id;
    }
  });

  return (
    <div ref={container} data-testid="case-map" className="h-full min-h-64 w-full rounded-md" />
  );
}

function pinElement(item: CaseView, selected: boolean, onSelect: (caseId: string) => void) {
  const element = document.createElement("button");
  const size = selected ? 22 : 12;
  element.type = "button";
  element.dataset.testid = selected ? "map-pin" : "map-dot";
  element.dataset.caseId = item.case_id;
  element.setAttribute("aria-label", `Case ${item.case_id}, ${item.priority ?? "no priority"}`);
  element.style.cssText = `width:${size}px;height:${size}px;border-radius:9999px;cursor:pointer;
    background:${item.priority ? PIN_COLOR[item.priority] : "#94a3b8"};
    border:${selected ? "3px solid white" : "1px solid rgba(15,23,42,.8)"};`;
  element.addEventListener("click", () => onSelect(item.case_id));
  return element;
}
