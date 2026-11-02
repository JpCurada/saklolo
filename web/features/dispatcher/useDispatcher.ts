"use client";

import { useCallback, useSyncExternalStore } from "react";

import { useSignedIn } from "../auth/AuthGate";

const KEY = "saklolo.dispatcher";
const listeners = new Set<() => void>();

function read(): string | undefined {
  try {
    return localStorage.getItem(KEY)?.trim() || undefined;
  } catch {
    // Private window or blocked storage: ask again next time.
    return undefined;
  }
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  window.addEventListener("storage", listener);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", listener);
  };
}

/**
 * The dispatcher on duty. Signed in with Cognito, it's the account's username. On an
 * open local API it's a typed name, remembered per browser; the server render has none.
 */
export function useDispatcher(): [string | undefined, (name: string | undefined) => void] {
  const signedIn = useSignedIn();
  const name = useSyncExternalStore(subscribe, read, () => undefined);

  const change = useCallback((next: string | undefined) => {
    const trimmed = next?.trim() || undefined;
    try {
      if (trimmed) localStorage.setItem(KEY, trimmed);
      else localStorage.removeItem(KEY);
    } catch {
      // Without storage the name can't be kept; the picker stays open.
    }
    listeners.forEach((listener) => listener());
  }, []);

  // Signed in, the account is the name: it can't be typed or changed here.
  return signedIn ? [signedIn.username, change] : [name, change];
}
