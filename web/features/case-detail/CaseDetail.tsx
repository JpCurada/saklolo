import type { ReactNode } from "react";

import {
  EmptyState,
  Icon,
  type IconName,
  Panel,
  PriorityBadge,
  StatusFlag,
  StatusFlagList,
  Text,
  Tile,
} from "@/components/ui";
import type { CaseView } from "@/lib/api/types";
import { BADGE_LABEL, LOCATION_SOURCE_LABEL } from "@/lib/format";

import { CaseHistory } from "./CaseHistory";
import { DispatchActions } from "./DispatchActions";
import { SourceList } from "./SourceList";

interface CaseDetailProps {
  item: CaseView | undefined;
  dispatcher: string | undefined;
  onChanged: () => void;
  onClosed: (dispatcher: string) => void;
}

export function CaseDetail({ item, dispatcher, onChanged, onClosed }: CaseDetailProps) {
  return (
    <Panel title="Case detail" testId="case-detail">
      {item ? (
        // The key restarts the fade, so a new case visibly replaces the last one.
        <div key={item.case_id} className="sk-fade">
          <Detail item={item} dispatcher={dispatcher} onChanged={onChanged} onClosed={onClosed} />
        </div>
      ) : (
        <EmptyState
          image="/assets/scene-no-selection.webp"
          alt=""
          title="No case selected"
          body="Select a case from the queue or the map."
        />
      )}
    </Panel>
  );
}

function Detail({ item, dispatcher, onChanged, onClosed }: CaseDetailProps & { item: CaseView }) {
  const place = item.location.barangay ?? "Location pending";
  const unassignedCritical =
    item.priority === "P1" && item.status === "open" && !item.assigned_team;
  return (
    <div className="space-y-4 p-4">
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <PriorityBadge priority={item.priority} urgent={unassignedCritical} />
          <span data-testid="case-status">
            <Text variant="caption" tone="muted">
              {item.case_id} · {item.status}
              {item.assigned_team ? ` · ${item.assigned_team}` : ""}
            </Text>
          </span>
        </div>
        <Text as="p" variant="title-m">
          {item.english_summary}
        </Text>
        <p>
          <Text tone="muted">Why this priority: </Text>
          <Text>
            {item.reason}
            {item.priority_overridden && " (set by dispatcher)"}
          </Text>
        </p>
        {item.badges.length > 0 && (
          <StatusFlagList>
            {item.badges.map((badge) => (
              <StatusFlag key={badge} flag={badge}>
                {BADGE_LABEL[badge]}
              </StatusFlag>
            ))}
          </StatusFlagList>
        )}
      </div>

      <div data-testid="case-facts" className="grid grid-cols-4 gap-2">
        <Fact label="People" icon="users">
          {item.people_count?.toString() ?? "Unknown"}
        </Fact>
        <Fact label="Vulnerable" icon="baby">
          {item.vulnerable.join(", ") || "None mentioned"}
        </Fact>
        <Fact label="Water" icon="droplet">
          {item.water_level}
        </Fact>
        <Fact label="Medical" icon="heart">
          {item.medical_emergency ? "Emergency" : "None mentioned"}
        </Fact>
      </div>

      <p data-testid="case-location" className="flex items-center gap-1">
        <Icon name="map-pin" />
        <Text tone="muted">Location: </Text>
        <Text>
          {place} ({LOCATION_SOURCE_LABEL[item.location.source ?? "unknown"]})
        </Text>
      </p>

      <DispatchActions
        key={item.case_id}
        item={item}
        dispatcher={dispatcher}
        onChanged={onChanged}
        onClosed={onClosed}
      />

      <CaseHistory events={item.history} />

      <div className="space-y-2">
        <h3>
          <Text variant="body-bold">Messages in this case ({item.sources.length})</Text>
        </h3>
        <SourceList sources={item.sources} />
      </div>
    </div>
  );
}

function Fact({ label, icon, children }: { label: string; icon: IconName; children: ReactNode }) {
  return (
    <Tile label={label}>
      <span className="inline-flex items-center gap-1 capitalize">
        <Icon name={icon} />
        {children}
      </span>
    </Tile>
  );
}
