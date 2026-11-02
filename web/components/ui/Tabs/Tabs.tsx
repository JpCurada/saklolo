import type { KeyboardEvent } from "react";

export interface TabItem<Id extends string> {
  id: Id;
  label: string;
  testId?: string;
}

interface TabsProps<Id extends string> {
  label: string;
  tabs: TabItem<Id>[];
  active: Id;
  onChange: (id: Id) => void;
}

/** Switches views in a panel. Arrow keys, Home, and End move between tabs. */
export function Tabs<Id extends string>({ label, tabs, active, onChange }: TabsProps<Id>) {
  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    const last = tabs.length - 1;
    const current = tabs.findIndex((tab) => tab.id === active);
    const next = {
      ArrowRight: current === last ? 0 : current + 1,
      ArrowLeft: current === 0 ? last : current - 1,
      Home: 0,
      End: last,
    }[event.key];
    if (next === undefined) return;
    event.preventDefault();
    onChange(tabs[next].id);
    event.currentTarget.querySelectorAll<HTMLElement>("[role=tab]")[next]?.focus();
  }

  return (
    <div
      role="tablist"
      aria-label={label}
      onKeyDown={onKeyDown}
      className="flex gap-(--sk-space-1)"
    >
      {tabs.map((tab) => {
        const selected = tab.id === active;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            data-testid={tab.testId}
            aria-selected={selected}
            tabIndex={selected ? 0 : -1}
            onClick={() => onChange(tab.id)}
            className={`rounded-(--sk-radius-pill) px-(--sk-space-3) py-(--sk-space-1) text-(length:--sk-text-caption-bold-size) font-(weight:--sk-text-caption-bold-weight) transition-colors duration-(--sk-motion-fast) focus-visible:outline-(length:--sk-stroke-2) focus-visible:outline-offset-(--sk-stroke-2) focus-visible:outline-(--sk-color-accent) ${
              selected
                ? "bg-(--sk-color-tab-active-bg) text-(--sk-color-tab-active-fg)"
                : "text-(--sk-color-ink-muted) hover:bg-(--sk-color-canvas)"
            }`}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
