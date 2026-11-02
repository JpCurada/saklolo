"use client";

import { type RefObject, useEffect } from "react";

const NEXT = new Set(["j", "ArrowDown"]);
const PREVIOUS = new Set(["k", "ArrowUp"]);

/** Typing, and arrow keys on the map or a control, must keep their own meaning. */
function ownsKeys(target: EventTarget | null): boolean {
  return (
    target instanceof HTMLElement &&
    (target.isContentEditable ||
      target.closest("input, textarea, select, [data-testid=case-map]") !== null)
  );
}

/** J/K or the arrow keys move the selection through the visible list. */
export function useQueueKeys(
  ids: string[],
  selectedId: string | undefined,
  onSelect: (caseId: string) => void,
  list: RefObject<HTMLElement | null>,
) {
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      const step = NEXT.has(event.key) ? 1 : PREVIOUS.has(event.key) ? -1 : 0;
      if (step === 0 || ids.length === 0) return;
      if (event.ctrlKey || event.metaKey || event.altKey || ownsKeys(event.target)) return;
      event.preventDefault();
      const current = selectedId === undefined ? -1 : ids.indexOf(selectedId);
      const next = ids[Math.min(Math.max(current + step, 0), ids.length - 1)];
      onSelect(next);
      list.current
        ?.querySelector(`[data-case-id="${CSS.escape(next)}"]`)
        ?.scrollIntoView({ block: "nearest" });
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [ids, selectedId, onSelect, list]);
}
