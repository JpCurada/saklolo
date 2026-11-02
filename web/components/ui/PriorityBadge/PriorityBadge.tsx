import type { Priority } from "@/lib/api/types";
import { PRIORITY_LABEL } from "@/lib/format";

import { Badge, type BadgeTone } from "../Badge/Badge";

const TONE: Record<Priority, BadgeTone> = {
  P1: "critical",
  P2: "high",
  P3: "moderate",
  P4: "info",
};

interface PriorityBadgeProps {
  priority: Priority | null;
  /** True for an unassigned P1 only (R21). */
  urgent?: boolean;
}

/** Text label always shown: color is never the only signal. */
export function PriorityBadge({ priority, urgent }: PriorityBadgeProps) {
  if (priority === null) {
    return (
      <Badge tone="none" testId="priority-badge">
        No priority
      </Badge>
    );
  }
  return (
    <Badge tone={TONE[priority]} urgent={urgent} testId="priority-badge" priority={priority}>
      {PRIORITY_LABEL[priority]}
    </Badge>
  );
}
