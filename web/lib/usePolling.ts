"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export const POLL_INTERVAL_MS = 2000;

export interface Polled<T> {
  data: T | undefined;
  error: string | undefined;
  refresh: () => Promise<void>;
}

/** Fetch now and every POLL_INTERVAL_MS; `refresh` re-fetches right after an action. */
export function usePolling<T>(fetcher: () => Promise<T>, intervalMs = POLL_INTERVAL_MS): Polled<T> {
  const [data, setData] = useState<T>();
  const [error, setError] = useState<string>();
  const fetcherRef = useRef(fetcher);
  useEffect(() => {
    fetcherRef.current = fetcher;
  }, [fetcher]);

  const refresh = useCallback(async () => {
    try {
      setData(await fetcherRef.current());
      setError(undefined);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = setInterval(() => void refresh(), intervalMs);
    return () => clearInterval(timer);
  }, [refresh, intervalMs]);

  return { data, error, refresh };
}
