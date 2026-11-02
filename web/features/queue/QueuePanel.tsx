"use client";

import { useState } from "react";

import { Panel } from "@/components/Panel";
import type { CaseView } from "@/lib/api/types";

import { QueueItem } from "./QueueItem";

type Lane = "queue" | "review";

interface QueuePanelProps {
  cases: CaseView[];
  selectedId: string | undefined;
  onSelect: (caseId: string) => void;
}

/** The dispatch queue, plus the human review lane for low-confidence triage. */
export function QueuePanel({ cases, selectedId, onSelect }: QueuePanelProps) {
  const [lane, setLane] = useState<Lane>("queue");
  const review = cases.filter((c) => c.badges.includes("needs_review"));
  const shown = lane === "queue" ? cases : review;

  const tabs = (
    <div role="tablist" className="flex gap-1 text-xs">
      <LaneTab id="queue" active={lane} onClick={setLane} label={`Queue (${cases.length})`} />
      <LaneTab
        id="review"
        active={lane}
        onClick={setLane}
        label={`Review lane (${review.length})`}
      />
    </div>
  );

  return (
    <Panel title="Dispatch" testId="dispatch-queue" actions={tabs}>
      <ul data-testid={lane === "queue" ? "queue-list" : "review-lane"}>
        {shown.map((item) => (
          <QueueItem
            key={item.case_id}
            item={item}
            selected={item.case_id === selectedId}
            onSelect={onSelect}
          />
        ))}
      </ul>
      {shown.length === 0 && (
        <p className="px-4 py-6 text-sm text-slate-500">
          {lane === "queue"
            ? "No open cases. Send a message or start a replay."
            : "Nothing needs review."}
        </p>
      )}
    </Panel>
  );
}

interface LaneTabProps {
  id: Lane;
  active: Lane;
  label: string;
  onClick: (lane: Lane) => void;
}

function LaneTab({ id, active, label, onClick }: LaneTabProps) {
  return (
    <button
      type="button"
      role="tab"
      data-testid={`${id}-tab`}
      aria-selected={active === id}
      onClick={() => onClick(id)}
      className={`rounded px-2 py-1 ${active === id ? "bg-sky-600 text-white" : "text-slate-400 hover:text-slate-200"}`}
    >
      {label}
    </button>
  );
}
