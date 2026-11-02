import type { Priority } from "@/lib/api/types";
import { PRIORITY_LABEL } from "@/lib/format";

const STYLE: Record<Priority, string> = {
  P1: "bg-red-600 text-white",
  P2: "bg-orange-500 text-slate-950",
  P3: "bg-yellow-300 text-slate-950",
  P4: "bg-slate-600 text-white",
};

/** Text label always shown: color is never the only signal. */
export function PriorityBadge({ priority }: { priority: Priority | null }) {
  if (priority === null) {
    return (
      <span
        data-testid="priority-badge"
        className="rounded px-2 py-0.5 text-xs font-semibold bg-slate-800 text-slate-300"
      >
        No priority
      </span>
    );
  }
  return (
    <span
      data-testid="priority-badge"
      data-priority={priority}
      className={`rounded px-2 py-0.5 text-xs font-bold tracking-wide ${STYLE[priority]}`}
    >
      {PRIORITY_LABEL[priority]}
    </span>
  );
}
