import { ListRow, PriorityBadge, Text } from "@/components/ui";
import type { CaseView } from "@/lib/api/types";
import { clockTime } from "@/lib/format";

import { CaseFlags } from "./CaseFlags";
import { isUnassignedCritical } from "./urgency";

interface QueueItemProps {
  item: CaseView;
  selected: boolean;
  /** The case arrived after the first load. */
  arrived: boolean;
  onSelect: (caseId: string) => void;
}

export function QueueItem({ item, selected, arrived, onSelect }: QueueItemProps) {
  return (
    <ListRow
      testId="queue-item"
      caseId={item.case_id}
      selected={selected}
      enter={arrived}
      onSelect={() => onSelect(item.case_id)}
      meta={
        <>
          <PriorityBadge priority={item.priority} urgent={isUnassignedCritical(item)} />
          <Text variant="caption" tone="muted">
            {item.location.barangay ?? "Location pending"} · {item.sources.length}{" "}
            {item.sources.length === 1 ? "message" : "messages"} · {clockTime(item.last_seen)}
          </Text>
        </>
      }
      trailing={
        item.status !== "open" && (
          <Text variant="caption-bold" tone="muted">
            {item.status}
          </Text>
        )
      }
    >
      <div className="sk-row-body">
        <div data-testid="case-summary">
          <Text as="p">{item.english_summary ?? "No summary yet"}</Text>
        </div>
        <div data-testid="case-reason">
          <Text as="p" variant="caption" tone="muted">
            Why: {item.reason || "not triaged yet"}
          </Text>
        </div>
        <CaseFlags badges={item.badges} />
      </div>
    </ListRow>
  );
}
