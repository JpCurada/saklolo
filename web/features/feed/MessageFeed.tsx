"use client";

import { useRef, useState, type ReactNode } from "react";

import { Button, Icon, ListRow, Panel, PriorityBadge, Skeleton, Text } from "@/components/ui";
import type { IconName } from "@/components/ui";
import type { Channel, MessageRecord } from "@/lib/api/types";
import { CHANNEL_LABEL, clockTime, shortSender } from "@/lib/format";

const SHOWN = 40;
/** Scrolled further than this, the reader has left the newest messages. */
const AWAY_PX = 8;

const CHANNEL_ICON: Record<Channel, IconName> = {
  sms: "phone",
  messenger: "message",
  telegram: "send",
  web: "signal",
};

function IconLabel({ icon, children }: { icon?: IconName; children: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1">
      {icon && <Icon name={icon} />}
      {children}
    </span>
  );
}

function Meta({ icon, children }: { icon?: IconName; children: string }) {
  return (
    <Text variant="caption" tone="faint">
      <IconLabel icon={icon}>{children}</IconLabel>
    </Text>
  );
}

function Flag({ icon, children }: { icon: IconName; children: string }) {
  return (
    <Text variant="caption-bold">
      <IconLabel icon={icon}>{children}</IconLabel>
    </Text>
  );
}

interface MessageFeedProps {
  messages: MessageRecord[];
  /** True until the first response arrives. */
  loading?: boolean;
}

/** The raw incoming stream, newest first: what volunteers used to read by hand. */
export function MessageFeed({ messages, loading = false }: MessageFeedProps) {
  const scroller = useRef<HTMLDivElement>(null);
  // Messages from the first load don't animate: only arrivals after it do.
  const [firstLoad, setFirstLoad] = useState<ReadonlySet<string>>();
  // Message count when the reader scrolled away; null while they're at the top.
  const [countWhenAway, setCountWhenAway] = useState<number | null>(null);

  if (!firstLoad && messages.length > 0) {
    setFirstLoad(new Set(messages.map((record) => record.message_id)));
  }

  const unseen = countWhenAway === null ? 0 : messages.length - countWhenAway;

  function trackScroll() {
    const away = (scroller.current?.scrollTop ?? 0) > AWAY_PX;
    setCountWhenAway((count) => (away ? (count ?? messages.length) : null));
  }

  function jumpToNewest() {
    if (scroller.current) scroller.current.scrollTop = 0;
  }

  return (
    <Panel title={`Incoming messages (${messages.length})`} testId="message-feed">
      <div className="relative h-full">
        {unseen > 0 && (
          <div className="absolute top-2 left-1/2 z-10 -translate-x-1/2">
            <Button
              variant="secondary"
              size="sm"
              testId="feed-jump"
              aria-label={`${unseen} new messages, jump to newest`}
              onClick={jumpToNewest}
            >
              {unseen} new
            </Button>
          </div>
        )}
        <div ref={scroller} onScroll={trackScroll} className="h-full overflow-y-auto">
          {loading && messages.length === 0 && <Skeleton lines={6} />}
          <ol>
            {messages.slice(0, SHOWN).map((record) => (
              <ListRow
                key={record.message_id}
                testId="feed-item"
                enter={firstLoad !== undefined && !firstLoad.has(record.message_id)}
                meta={
                  <>
                    <Meta>{clockTime(record.message.received_at)}</Meta>
                    <Meta>{shortSender(record.message.sender)}</Meta>
                    <Meta icon={CHANNEL_ICON[record.message.channel]}>
                      {CHANNEL_LABEL[record.message.channel]}
                    </Meta>
                    {record.kind === "location_reply" && <Meta>location reply</Meta>}
                    {record.error && <Flag icon="flag">kept for review</Flag>}
                    {record.outcome?.is_suspicious && <Flag icon="shield">suspicious</Flag>}
                  </>
                }
                trailing={
                  record.outcome?.priority && <PriorityBadge priority={record.outcome.priority} />
                }
              >
                <Text as="p" lang="fil" clamp>
                  {record.message.text}
                </Text>
              </ListRow>
            ))}
          </ol>
        </div>
      </div>
    </Panel>
  );
}
