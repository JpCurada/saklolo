"use client";

import { useState } from "react";

interface Seen {
  key: string;
  ids: Set<string>;
  arrived: Set<string>;
}

const NONE = new Set<string>();

/** IDs new since the previous list. Empty on the first load, so nothing animates then. */
export function useArrivals(ids: string[], loaded: boolean): Set<string> {
  const [seen, setSeen] = useState<Seen>();
  const key = ids.join();
  if (loaded && seen?.key !== key) {
    setSeen({
      key,
      ids: new Set([...(seen?.ids ?? []), ...ids]),
      arrived: new Set(seen ? ids.filter((id) => !seen.ids.has(id)) : []),
    });
  }
  return seen?.arrived ?? NONE;
}
