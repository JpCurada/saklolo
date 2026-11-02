import { PriorityBadge, Text, Tile } from "@/components/ui";
import type { SourceView } from "@/lib/api/types";
import { CHANNEL_LABEL, clockTime, shortSender } from "@/lib/format";

import { AgentTrace } from "./AgentTrace";

/** Every message merged into the case: the resident's words next to the English reading. */
export function SourceList({ sources }: { sources: SourceView[] }) {
  return (
    <ol data-testid="source-list" className="space-y-2">
      {sources.map((source) => (
        <li
          key={source.message_id}
          data-testid="source-item"
          className="sk-source-item grid grid-cols-2 gap-2"
        >
          <Tile
            label={`Original · ${shortSender(source.sender)} · ${CHANNEL_LABEL[source.channel]} · ${clockTime(source.received_at)}`}
          >
            <span data-testid="source-original">
              <Text lang="fil">{source.text}</Text>
            </span>
          </Tile>
          <Tile label="English summary">
            <span className="flex flex-col items-start gap-1">
              {source.priority && <PriorityBadge priority={source.priority} />}
              <span data-testid="source-summary">
                <Text>{source.english_summary ?? "Location reply (no summary)"}</Text>
              </span>
            </span>
          </Tile>
          <AgentTrace trace={source.trace ?? []} />
        </li>
      ))}
    </ol>
  );
}
