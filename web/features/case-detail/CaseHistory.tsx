import { Disclosure, Icon, type IconName, Text } from "@/components/ui";
import type { CaseEvent } from "@/lib/api/types";
import { clockTime } from "@/lib/format";

const VERB: Record<CaseEvent["action"], string> = {
  assigned: "assigned",
  overridden: "set priority",
  closed: "closed the case",
};

const ICON: Record<CaseEvent["action"], IconName> = {
  assigned: "users",
  overridden: "flag",
  closed: "check",
};

/** Every decision on this case, oldest first, with the person who made it. */
export function CaseHistory({ events }: { events: CaseEvent[] }) {
  if (events.length === 0) return null;
  return (
    <Disclosure title="Decisions" meta={`(${events.length})`} defaultOpen>
      <ol data-testid="case-history" className="space-y-1">
        {events.map((event, index) => (
          <li
            key={`${event.at}-${index}`}
            data-testid="history-item"
            className="flex items-center gap-2"
          >
            <Icon name={ICON[event.action]} />
            <Text variant="caption" tone="faint">
              {clockTime(event.at)}
            </Text>
            <Text variant="caption-bold">{event.dispatcher}</Text>
            <Text variant="caption">
              {VERB[event.action]}: {event.detail}
            </Text>
          </li>
        ))}
      </ol>
    </Disclosure>
  );
}
