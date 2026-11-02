import type { CaseView } from "@/lib/api/types";

/** A P1 nobody has taken yet: the only case allowed to pulse (design/DESIGN.md, R21). */
export function isUnassignedCritical(item: CaseView): boolean {
  return item.priority === "P1" && item.status === "open" && !item.assigned_team;
}
