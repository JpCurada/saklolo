"use client";

import { useState } from "react";

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
  const status = usePolling(api.replay);
  const running = status.data?.running ?? false;

  async function run(action: () => Promise<unknown>) {
    try {
      await action();
      setError(undefined);
      await status.refresh();
      onTick();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    }
  }

  return (
    <div data-testid="replay-controls" className="flex items-center gap-2 text-xs">
      <span
        data-testid="sped-up-label"
        className="rounded bg-amber-400 px-2 py-0.5 font-bold text-slate-950"
      >
        REPLAY · SPED UP · SYNTHETIC DATA
      </span>
      <label className="sr-only" htmlFor="replay-speed">
        Replay speed
      </label>
      <select
        id="replay-speed"
        data-testid="replay-speed"
        value={speed}
        onChange={(event) => setSpeed(Number(event.target.value))}
        disabled={running}
        className="rounded border border-slate-700 bg-slate-950 px-2 py-1"
      >
        {SPEEDS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {running ? (
        <button
          type="button"
          data-testid="replay-stop"
          onClick={() => void run(api.stopReplay)}
          className="rounded border border-slate-600 px-3 py-1 hover:bg-slate-800"
        >
          Stop
        </button>
      ) : (
        <button
          type="button"
          data-testid="replay-start"
          onClick={() => void run(() => api.startReplay({ split: "dev", speed, max_delay_s: 2 }))}
          className="rounded bg-sky-600 px-3 py-1 font-semibold text-white hover:bg-sky-500"
        >
          Replay dev split
        </button>
      )}
      <span data-testid="replay-status" className="tabular-nums text-slate-400">
        {status.data ? `${status.data.sent} / ${status.data.total} messages` : "–"}
      </span>
      {error && (
        <span role="alert" className="text-red-400">
          {error}
        </span>
      )}
    </div>
  );
}
