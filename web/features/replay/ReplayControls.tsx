"use client";

import { useState } from "react";

import { Badge, Button, Select, Text } from "@/components/ui";
import { api } from "@/lib/api/client";
import { usePolling } from "@/lib/usePolling";

// Storm seconds per real second.
const SPEEDS = [
  { value: 600, label: "10 storm minutes / s" },
  { value: 3600, label: "1 storm hour / s" },
  { value: 21600, label: "6 storm hours / s" },
];

/** Replays the synthetic dev split. Always labelled "sped up" so the video stays honest. */
export function ReplayControls({ onTick }: { onTick: () => void }) {
  const [speed, setSpeed] = useState(3600);
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);
  const status = usePolling(api.replay);
  const running = status.data?.running ?? false;
  const total = status.data?.total ?? 0;

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    try {
      await action();
      setError(undefined);
      await status.refresh();
      onTick();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div data-testid="replay-controls" className="sk-replay">
      <Badge tone="none" testId="sped-up-label">
        Replay · sped up
      </Badge>
      <label className="sr-only" htmlFor="replay-speed">
        Replay speed
      </label>
      <Select
        id="replay-speed"
        testId="replay-speed"
        value={speed}
        onChange={(event) => setSpeed(Number(event.target.value))}
        disabled={running}
      >
        {SPEEDS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </Select>
      {running ? (
        <Button
          variant="secondary"
          size="sm"
          testId="replay-stop"
          loading={busy}
          onClick={() => void run(api.stopReplay)}
        >
          Stop
        </Button>
      ) : (
        <Button
          variant="secondary"
          size="sm"
          testId="replay-start"
          loading={busy}
          onClick={() => void run(() => api.startReplay({ split: "dev", speed, max_delay_s: 2 }))}
        >
          Replay dev split
        </Button>
      )}
      {total > 0 && (
        <progress
          data-testid="replay-progress"
          aria-label="Replay progress"
          className="sk-replay-progress"
          value={status.data?.sent ?? 0}
          max={total}
        />
      )}
      <span data-testid="replay-status" className="tabular-nums">
        <Text variant="caption" tone="muted">
          {status.data ? `${status.data.sent} / ${status.data.total} messages` : "–"}
        </Text>
      </span>
      {error && (
        <span role="alert">
          <Text variant="caption-bold">{error}</Text>
        </span>
      )}
    </div>
  );
}
