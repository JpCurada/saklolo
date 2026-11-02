"use client";

import { useState } from "react";

import { api } from "@/lib/api/client";
import type { CaseView, Priority } from "@/lib/api/types";
import { PRIORITY_LABEL } from "@/lib/format";

interface DispatchActionsProps {
  item: CaseView;
  onChanged: () => void;
}

const PRIORITIES: Priority[] = ["P1", "P2", "P3", "P4"];

/** The dispatcher decides: assign a team, correct the priority, or confirm the household safe. */
export function DispatchActions({ item, onChanged }: DispatchActionsProps) {
  const [team, setTeam] = useState("Team Bravo");
  const [priority, setPriority] = useState<Priority>(item.priority ?? "P2");
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string>();
  const closed = item.status === "closed";

  async function act(action: () => Promise<unknown>) {
    try {
      await action();
      setError(undefined);
      onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    }
  }

  return (
    <div data-testid="dispatch-actions" className="space-y-3">
      <form
        className="flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void act(() => api.assign(item.case_id, team));
        }}
      >
        <label className="sr-only" htmlFor="assign-team">
          Rescue team
        </label>
        <input
          id="assign-team"
          data-testid="assign-team"
          value={team}
          onChange={(event) => setTeam(event.target.value)}
          className="flex-1 rounded border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm"
        />
        <button
          type="submit"
          data-testid="assign-button"
          disabled={closed || !team.trim()}
          className="rounded bg-sky-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-sky-500 disabled:opacity-40"
        >
          Assign team
        </button>
      </form>

      <form
        className="flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void act(() => api.override(item.case_id, priority, reason));
        }}
      >
        <label className="sr-only" htmlFor="override-priority">
          New priority
        </label>
        <select
          id="override-priority"
          data-testid="override-priority"
          value={priority}
          onChange={(event) => setPriority(event.target.value as Priority)}
          className="rounded border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm"
        >
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {PRIORITY_LABEL[p]}
            </option>
          ))}
        </select>
        <label className="sr-only" htmlFor="override-reason">
          Reason
        </label>
        <input
          id="override-reason"
          data-testid="override-reason"
          placeholder="Reason for the change"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          className="flex-1 rounded border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm"
        />
        <button
          type="submit"
          data-testid="override-button"
          disabled={!reason.trim()}
          className="rounded border border-slate-600 px-3 py-1.5 text-sm hover:bg-slate-800 disabled:opacity-40"
        >
          Override
        </button>
      </form>

      <button
        type="button"
        data-testid="confirm-safe-button"
        disabled={closed}
        onClick={() => void act(() => api.confirmSafe(item.case_id))}
        className={`w-full rounded px-3 py-1.5 text-sm font-semibold disabled:opacity-40 ${
          item.badges.includes("reported_safe")
            ? "bg-emerald-600 text-white hover:bg-emerald-500"
            : "border border-slate-600 text-slate-300 hover:bg-slate-800"
        }`}
      >
        {closed ? "Closed" : "Confirm safe and close case"}
      </button>
      {error && (
        <p role="alert" className="text-xs text-red-400">
          {error}
        </p>
      )}
    </div>
  );
}
