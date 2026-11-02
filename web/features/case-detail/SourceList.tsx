import { PriorityBadge } from "@/components/PriorityBadge";
import type { SourceView } from "@/lib/api/types";
import { clockTime, shortSender } from "@/lib/format";

/** Every message merged into the case: the resident's words next to the English reading. */
export function SourceList({ sources }: { sources: SourceView[] }) {
  return (
    <ol data-testid="source-list" className="space-y-2">
      {sources.map((source) => (
        <li
          key={source.message_id}
          data-testid="source-item"
          className="grid grid-cols-2 gap-3 rounded-md border border-slate-800 bg-slate-950/60 p-3"
        >
          <div>
            <p className="mb-1 text-[11px] uppercase tracking-wide text-slate-500">
              Original · {shortSender(source.sender)} · {source.channel} ·{" "}
              {clockTime(source.received_at)}
            </p>
            <p data-testid="source-original" lang="fil" className="text-sm text-slate-200">
              {source.text}
            </p>
          </div>
          <div>
            <div className="mb-1 flex items-center gap-2">
              <span className="text-[11px] uppercase tracking-wide text-slate-500">
                English summary
              </span>
              {source.priority && <PriorityBadge priority={source.priority} />}
            </div>
            <p data-testid="source-summary" className="text-sm text-slate-300">
              {source.english_summary ?? "Location reply (no summary)"}
            </p>
          </div>
        </li>
      ))}
    </ol>
  );
}
