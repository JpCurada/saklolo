import { Panel } from "@/components/Panel";
import { PriorityBadge } from "@/components/PriorityBadge";
import type { MessageRecord } from "@/lib/api/types";
import { clockTime, shortSender } from "@/lib/format";

const SHOWN = 40;

/** The raw incoming stream, newest first: what volunteers used to read by hand. */
export function MessageFeed({ messages }: { messages: MessageRecord[] }) {
  return (
    <Panel title={`Incoming messages (${messages.length})`} testId="message-feed">
      <ol>
        {messages.slice(0, SHOWN).map((record) => (
          <li
            key={record.message_id}
            data-testid="feed-item"
            className="border-b border-slate-800 px-4 py-2"
          >
            <div className="mb-0.5 flex items-center gap-2 text-[11px] text-slate-500">
              <span>{clockTime(record.message.received_at)}</span>
              <span>{shortSender(record.message.sender)}</span>
              <span className="uppercase">{record.message.channel}</span>
              {record.kind === "location_reply" && (
                <span className="text-amber-300">location reply</span>
              )}
              {record.error && <span className="text-red-400">kept for review</span>}
              {record.outcome?.is_suspicious && (
                <span className="text-fuchsia-300">suspicious</span>
              )}
              <span className="ml-auto">
                {record.outcome?.priority && <PriorityBadge priority={record.outcome.priority} />}
              </span>
            </div>
            <p lang="fil" className="line-clamp-2 text-xs text-slate-300">
              {record.message.text}
            </p>
          </li>
        ))}
      </ol>
    </Panel>
  );
}
