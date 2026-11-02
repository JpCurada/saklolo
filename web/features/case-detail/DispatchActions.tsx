"use client";

import { type KeyboardEvent, type MouseEvent, useEffect, useRef, useState } from "react";

import { Button, Icon, Input, Select, Text } from "@/components/ui";
import { api } from "@/lib/api/client";
import type { CaseView, Priority } from "@/lib/api/types";
import { PRIORITY_LABEL } from "@/lib/format";

interface DispatchActionsProps {
  item: CaseView;
  /** Who is on duty. Without a name, nothing can be decided. */
  dispatcher: string | undefined;
  onChanged: () => void;
  /** The list drops a closed case, so whoever shows the list confirms it. */
  onClosed: (dispatcher: string) => void;
}

const PRIORITIES: Priority[] = ["P1", "P2", "P3", "P4"];

type Action = "assign" | "override" | "close";

/** The dispatcher decides: assign a team, correct the priority, or confirm the household safe. */
export function DispatchActions({ item, dispatcher, onChanged, onClosed }: DispatchActionsProps) {
  const [team, setTeam] = useState("Team Bravo");
  const [priority, setPriority] = useState<Priority>(item.priority ?? "P2");
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string>();
  const [pending, setPending] = useState<Action>();
  const [done, setDone] = useState({ count: 0, message: "" });
  const [closeArmed, setCloseArmed] = useState(false);
  const closeButton = useRef<HTMLButtonElement>(null);
  const cancelButton = useRef<HTMLButtonElement>(null);
  const closed = item.status === "closed";
  const reasonMissing = priority !== item.priority && !reason.trim();
  const reportedSafe = item.badges.includes("reported_safe");
  const nameless = !dispatcher;

  // Focus leaves the close button, so a second Enter cancels instead of confirming.
  useEffect(() => {
    if (closeArmed) cancelButton.current?.focus();
  }, [closeArmed]);

  async function act(name: Action, action: () => Promise<unknown>, message?: string) {
    setPending(name);
    try {
      await action();
      setError(undefined);
      if (message) setDone(({ count }) => ({ count: count + 1, message }));
      onChanged();
      return true;
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
      return false;
    } finally {
      setPending(undefined);
    }
  }

  async function pressClose(event: MouseEvent) {
    // The second click of a double-click must not count as the confirmation.
    if (event.detail > 1) return;
    if (!dispatcher) return;
    if (!closeArmed) {
      setCloseArmed(true);
      return;
    }
    setCloseArmed(false);
    if (await act("close", () => api.confirmSafe(item.case_id, dispatcher))) onClosed(dispatcher);
  }

  function holdClose(event: KeyboardEvent) {
    // A held key repeats. Only a fresh press can act on a rescue case.
    if (event.repeat) event.preventDefault();
  }

  function cancelClose() {
    setCloseArmed(false);
    closeButton.current?.focus();
  }

  return (
    <div data-testid="dispatch-actions" className="space-y-3">
      {nameless && (
        <p data-testid="dispatcher-needed" className="flex items-center gap-1">
          <Icon name="users" />
          <Text variant="caption-bold">Start your shift in the header to act on cases.</Text>
        </p>
      )}
      <form
        className="flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          if (!dispatcher) return;
          void act(
            "assign",
            () => api.assign(item.case_id, team, dispatcher),
            `${team.trim()} assigned by ${dispatcher}.`,
          );
        }}
      >
        <label className="sr-only" htmlFor="assign-team">
          Rescue team
        </label>
        <div className="min-w-0 flex-1">
          <Input
            id="assign-team"
            testId="assign-team"
            value={team}
            onChange={(event) => setTeam(event.target.value)}
          />
        </div>
        <Button
          type="submit"
          variant={reportedSafe ? "secondary" : "primary"}
          testId="assign-button"
          loading={pending === "assign"}
          disabled={nameless || closed || !team.trim()}
        >
          Assign team
        </Button>
      </form>

      <form
        className="space-y-1"
        onSubmit={async (event) => {
          event.preventDefault();
          if (!dispatcher) return;
          const saved = await act(
            "override",
            () => api.override(item.case_id, priority, reason, dispatcher),
            `Priority set to ${PRIORITY_LABEL[priority]} by ${dispatcher}.`,
          );
          if (saved) setReason("");
        }}
      >
        <div className="sk-dispatch-override flex gap-2">
          <label className="sr-only" htmlFor="override-priority">
            New priority
          </label>
          <Select
            id="override-priority"
            testId="override-priority"
            value={priority}
            onChange={(event) => setPriority(event.target.value as Priority)}
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {PRIORITY_LABEL[p]}
              </option>
            ))}
          </Select>
          <label className="sr-only" htmlFor="override-reason">
            Reason
          </label>
          <div className="min-w-0 flex-1">
            <Input
              id="override-reason"
              testId="override-reason"
              placeholder="Reason for the change"
              value={reason}
              aria-describedby={reasonMissing ? "override-hint" : undefined}
              onChange={(event) => setReason(event.target.value)}
            />
          </div>
          <Button
            type="submit"
            variant="secondary"
            testId="override-button"
            loading={pending === "override"}
            disabled={nameless || !reason.trim()}
          >
            Override
          </Button>
        </div>
        {reasonMissing && (
          <p id="override-hint" data-testid="override-hint">
            <Text variant="caption" tone="muted">
              Add a reason to change the priority.
            </Text>
          </p>
        )}
      </form>

      <div className="flex gap-2">
        <Button
          block
          variant={closeArmed ? "danger" : reportedSafe ? "primary" : "secondary"}
          testId="confirm-safe-button"
          ref={closeButton}
          loading={pending === "close"}
          disabled={nameless || closed}
          onClick={(event) => void pressClose(event)}
          onKeyDown={holdClose}
        >
          {closed ? "Closed" : closeArmed ? "Confirm close" : "Confirm safe and close case"}
        </Button>
        {closeArmed && (
          <Button
            variant="ghost"
            testId="confirm-safe-cancel"
            ref={cancelButton}
            onClick={cancelClose}
          >
            Cancel
          </Button>
        )}
      </div>

      {done.count > 0 && (
        // The key replays the pop for each confirmation, even with the same words.
        <p
          key={done.count}
          role="status"
          data-testid="action-confirmation"
          className="sk-pop flex items-center gap-1"
        >
          <Icon name="check" />
          <Text variant="caption-bold">{done.message}</Text>
        </p>
      )}
      {error && (
        <p role="alert" className="flex items-center gap-1">
          <Icon name="alert" />
          <Text variant="caption">{error}</Text>
        </p>
      )}
    </div>
  );
}
