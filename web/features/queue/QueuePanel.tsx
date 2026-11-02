"use client";

import { useRef, useState } from "react";

import { EmptyState, Icon, Panel, Skeleton, Tabs, Text } from "@/components/ui";
import type { CaseView } from "@/lib/api/types";

import { QueueItem } from "./QueueItem";
import { useArrivals } from "./useArrivals";
import { useQueueKeys } from "./useQueueKeys";

type Lane = "queue" | "review";

const NO_API = "/assets/scene-api-down.webp";
const QUEUE_CLEAR = "/assets/scene-queue-clear.webp";
const REVIEW_CLEAR = "/assets/scene-review-clear.webp";

interface QueuePanelProps {
  cases: CaseView[];
  /** The first response hasn't come back yet. */
  loading: boolean;
  error: string | undefined;
  selectedId: string | undefined;
  onSelect: (caseId: string) => void;
}

/** The dispatch queue, plus the human review lane for low-confidence triage. */
export function QueuePanel({ cases, loading, error, selectedId, onSelect }: QueuePanelProps) {
  const [lane, setLane] = useState<Lane>("queue");
  const listRef = useRef<HTMLUListElement>(null);
  const review = cases.filter((c) => c.badges.includes("needs_review"));
  const shown = lane === "queue" ? cases : review;
  // Rows from the last good poll stay on screen, so only an empty queue gets the scene.
  const down = Boolean(error) && cases.length === 0;
  const arrived = useArrivals(
    cases.map((c) => c.case_id),
    !loading,
  );
  useQueueKeys(
    shown.map((c) => c.case_id),
    selectedId,
    onSelect,
    listRef,
  );

  const tabs = (
    <Tabs
      label="Dispatch lanes"
      active={lane}
      onChange={setLane}
      tabs={[
        { id: "queue", label: `Queue (${cases.length})`, testId: "queue-tab" },
        { id: "review", label: `Review lane (${review.length})`, testId: "review-tab" },
      ]}
    />
  );

  return (
    <Panel title="Dispatch" testId="dispatch-queue" actions={tabs}>
      {error && !down && (
        <p role="alert" data-testid="api-error" className="flex items-center gap-2 px-4 py-2">
          <Icon name="alert" size="sm" />
          <Text variant="caption-bold">
            Can&apos;t reach the Saklolo API. Showing the last update.
          </Text>
        </p>
      )}
      {down && (
        <div role="alert">
          <EmptyState
            image={NO_API}
            alt=""
            title="Can't reach the Saklolo API"
            body={`${error}. Start it with make demo.`}
            testId="api-error"
          />
        </div>
      )}
      {loading && !error && <Skeleton lines={9} />}
      <ul ref={listRef} data-testid={lane === "queue" ? "queue-list" : "review-lane"}>
        {shown.map((item) => (
          <QueueItem
            key={item.case_id}
            item={item}
            selected={item.case_id === selectedId}
            arrived={arrived.has(item.case_id)}
            onSelect={onSelect}
          />
        ))}
      </ul>
      {shown.length > 1 && (
        <div className="sk-queue-hint">
          <Text as="p" variant="caption" tone="faint">
            J and K, or the arrow keys, move through cases.
          </Text>
        </div>
      )}
      {shown.length === 0 && !loading && !down && (
        <EmptyState
          image={lane === "queue" ? QUEUE_CLEAR : REVIEW_CLEAR}
          alt=""
          title={lane === "queue" ? "No open cases" : "Nothing needs review"}
          body={
            lane === "queue"
              ? "Send a message or start a replay."
              : "Low-confidence triage lands here for a human decision."
          }
        />
      )}
    </Panel>
  );
}
