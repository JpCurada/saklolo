import type { Badge } from "@/lib/api/types";
import { BADGE_LABEL } from "@/lib/format";

const STYLE: Record<Badge, string> = {
  corroborated: "border-emerald-400 text-emerald-300",
  suspicious: "border-fuchsia-400 text-fuchsia-300",
  reported_safe: "border-sky-400 text-sky-300",
  awaiting_location: "border-amber-400 text-amber-300",
  needs_review: "border-violet-400 text-violet-300",
  overridden: "border-slate-400 text-slate-300",
};

export function CaseBadges({ badges }: { badges: Badge[] }) {
  if (badges.length === 0) return null;
  return (
    <ul data-testid="case-badges" className="flex flex-wrap gap-1.5">
      {badges.map((badge) => (
        <li
          key={badge}
          data-testid="badge"
          data-badge={badge}
          className={`rounded-full border px-2 py-0.5 text-[11px] font-medium ${STYLE[badge]}`}
        >
          {BADGE_LABEL[badge]}
        </li>
      ))}
    </ul>
  );
}
