import type { CaseView } from "@/lib/api/types";

/** Headline counts for the open queue. */
export function StatsBar({ cases }: { cases: CaseView[] }) {
  const stats = [
    { id: "stat-open", label: "Open cases", value: cases.length, tone: "text-white" },
    {
      id: "stat-critical",
      label: "Critical",
      value: cases.filter((c) => c.priority === "P1").length,
      tone: "text-red-400",
    },
    {
      id: "stat-review",
      label: "Needs review",
      value: cases.filter((c) => c.badges.includes("needs_review")).length,
      tone: "text-violet-300",
    },
    {
      id: "stat-awaiting",
      label: "Awaiting location",
      value: cases.filter((c) => c.badges.includes("awaiting_location")).length,
      tone: "text-amber-300",
    },
  ];
  return (
    <dl className="flex gap-5">
      {stats.map((stat) => (
        <div key={stat.id} data-testid={stat.id} className="flex items-baseline gap-1.5">
          <dd className={`text-lg font-bold tabular-nums ${stat.tone}`}>{stat.value}</dd>
          <dt className="text-xs text-slate-400">{stat.label}</dt>
        </div>
      ))}
    </dl>
  );
}
