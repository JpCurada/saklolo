import { CaseBadges } from "@/components/CaseBadges";
import { Panel } from "@/components/Panel";
import { PriorityBadge } from "@/components/PriorityBadge";
import type { CaseView } from "@/lib/api/types";
import { LOCATION_SOURCE_LABEL } from "@/lib/format";

import { DispatchActions } from "./DispatchActions";
import { SourceList } from "./SourceList";

interface CaseDetailProps {
  item: CaseView | undefined;
  onChanged: () => void;
}

export function CaseDetail({ item, onChanged }: CaseDetailProps) {
  return (
    <Panel title="Case detail" testId="case-detail">
      {item ? <Detail item={item} onChanged={onChanged} /> : <Empty />}
    </Panel>
  );
}

function Detail({ item, onChanged }: { item: CaseView; onChanged: () => void }) {
  const place = item.location.barangay ?? "Location pending";
  return (
    <div className="space-y-4 p-4">
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <PriorityBadge priority={item.priority} />
          <span
            data-testid="case-status"
            className="text-xs uppercase tracking-wide text-slate-400"
          >
            {item.case_id} · {item.status}
            {item.assigned_team ? ` · ${item.assigned_team}` : ""}
          </span>
        </div>
        <p className="text-lg font-semibold leading-snug text-white">{item.english_summary}</p>
        <p className="text-sm text-slate-300">
          <span className="text-slate-500">Why this priority: </span>
          {item.reason}
          {item.priority_overridden && " (set by dispatcher)"}
        </p>
        <CaseBadges badges={item.badges} />
      </div>

      <dl data-testid="case-facts" className="grid grid-cols-4 gap-2 text-sm">
        <Fact label="People" value={item.people_count?.toString() ?? "Unknown"} />
        <Fact label="Vulnerable" value={item.vulnerable.join(", ") || "None mentioned"} />
        <Fact label="Water" value={item.water_level} />
        <Fact label="Medical" value={item.medical_emergency ? "Emergency" : "None mentioned"} />
      </dl>

      <p data-testid="case-location" className="text-sm text-slate-300">
        <span className="text-slate-500">Location: </span>
        {place} ({LOCATION_SOURCE_LABEL[item.location.source ?? "unknown"]})
      </p>

      <DispatchActions key={item.case_id} item={item} onChanged={onChanged} />

      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Messages in this case ({item.sources.length})
        </h3>
        <SourceList sources={item.sources} />
      </div>
    </div>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-slate-950/60 px-3 py-2">
      <dt className="text-[11px] uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="capitalize text-slate-200">{value}</dd>
    </div>
  );
}

function Empty() {
  return <p className="p-4 text-sm text-slate-500">Select a case from the queue or the map.</p>;
}
