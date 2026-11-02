import { StatCard } from "@/components/ui";
import type { CaseView } from "@/lib/api/types";

/** Headline counts for the open queue. */
export function StatsBar({ cases }: { cases: CaseView[] }) {
  const count = (test: (item: CaseView) => boolean) => cases.filter(test).length;
  return (
    <dl className="sk-stats">
      <StatCard compact testId="stat-open" label="Open cases" value={cases.length} />
      <StatCard
        compact
        critical
        testId="stat-critical"
        label="Critical"
        value={count((c) => c.priority === "P1")}
      />
      <StatCard
        compact
        testId="stat-review"
        label="Needs review"
        value={count((c) => c.badges.includes("needs_review"))}
      />
      <StatCard
        compact
        testId="stat-awaiting"
        label="Awaiting location"
        value={count((c) => c.badges.includes("awaiting_location"))}
      />
    </dl>
  );
}
