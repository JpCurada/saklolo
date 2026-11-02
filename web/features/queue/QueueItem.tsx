import { CaseBadges } from "@/components/CaseBadges";
import { PriorityBadge } from "@/components/PriorityBadge";
import type { CaseView } from "@/lib/api/types";
import { clockTime } from "@/lib/format";

interface QueueItemProps {
  item: CaseView;
  selected: boolean;
  onSelect: (caseId: string) => void;
}

export function QueueItem({ item, selected, onSelect }: QueueItemProps) {
  return (
    <li>
      <button
        type="button"
        data-testid="queue-item"
        data-case-id={item.case_id}
        aria-pressed={selected}
        onClick={() => onSelect(item.case_id)}
        className={`w-full space-y-1.5 border-b border-slate-800 px-4 py-3 text-left transition-colors hover:bg-slate-800/60 ${
          selected ? "bg-slate-800 ring-1 ring-inset ring-sky-500" : ""
        }`}
      >
        <div className="flex items-center gap-2">
          <PriorityBadge priority={item.priority} />
          <span className="text-xs text-slate-400">
            {item.location.barangay ?? "Location pending"} · {item.sources.length}{" "}
            {item.sources.length === 1 ? "message" : "messages"} · {clockTime(item.last_seen)}
          </span>
          {item.status !== "open" && (
            <span className="ml-auto text-[11px] uppercase text-sky-300">{item.status}</span>
          )}
        </div>
        <p data-testid="case-summary" className="text-sm leading-snug text-slate-100">
          {item.english_summary ?? "No summary yet"}
        </p>
        <p data-testid="case-reason" className="text-xs text-slate-400">
          Why: {item.reason || "not triaged yet"}
        </p>
        <CaseBadges badges={item.badges} />
      </button>
    </li>
  );
}
