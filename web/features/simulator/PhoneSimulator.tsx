"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  Bubble,
  Button,
  Icon,
  Input,
  PhoneFrame,
  type IconName,
  PhoneSkin,
  Text,
} from "@/components/ui";
import { api } from "@/lib/api/client";
import type { Channel } from "@/lib/api/types";
import { clockTime } from "@/lib/format";
import { usePolling } from "@/lib/usePolling";

// Synthetic examples. They fill the input; a person still presses Send.
const SAMPLES = [
  "Tulong po, nasa bubong na kami sa Malanday",
  "Tumataas pa tubig dito sa Tumana, may senior kami",
  "Pwede po ba kami lumikas? 3 kami dito",
];

interface ThreadMessage {
  direction: "out" | "in";
  body: string;
  at: string;
}

/** How each chat app introduces the conversation and its message box. */
const LOOK: Record<
  PhoneSkin,
  { status: string; placeholder: string; style: string; tools: IconName[] }
> = {
  sms: { status: "+63 900 000 0911", placeholder: "Text message", style: "SMS", tools: ["plus"] },
  telegram: { status: "bot", placeholder: "Message", style: "Telegram-style", tools: [] },
  messenger: {
    status: "Active now",
    placeholder: "Aa",
    style: "Messenger-style",
    tools: ["plus", "camera"],
  },
};

interface PhoneSimulatorProps {
  channel: Channel & PhoneSkin;
  testId: string;
  /** A clearly fake sender: a number outside the dataset's range, or a `demo-` account. */
  defaultSender: string;
  onSent?: () => void;
}

/** A simulated phone: sends to the real intake on its channel, shows what comes back. */
export function PhoneSimulator({ channel, testId, defaultSender, onSent }: PhoneSimulatorProps) {
  const [sender, setSender] = useState(defaultSender);
  const [draft, setDraft] = useState("");
  const [sent, setSent] = useState<ThreadMessage[]>([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string>();
  const fetchReplies = useCallback(() => api.outbox(sender), [sender]);
  const replies = usePolling(fetchReplies);
  const threadEnd = useRef<HTMLOListElement>(null);

  const thread = [
    ...sent,
    ...(replies.data ?? []).map((m) => ({ direction: "in" as const, body: m.body, at: m.sent_at })),
  ].sort((a, b) => a.at.localeCompare(b.at));

  useEffect(() => {
    const element = threadEnd.current;
    if (element) element.scrollTop = element.scrollHeight; // newest message stays in view
  }, [thread.length, sending]);

  async function send() {
    const text = draft.trim();
    if (!text || sending) return;
    setSending(true);
    try {
      const result = await api.send({ sender, text, channel });
      setSent((previous) => [
        ...previous,
        { direction: "out", body: text, at: result.record.message.received_at },
      ]);
      setDraft("");
      setError(undefined);
      await replies.refresh();
      onSent?.();
    } catch (caught) {
      // The draft stays, so Retry resends the same text.
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setSending(false);
    }
  }

  const look = LOOK[channel];
  const lastOut = thread.map((message) => message.direction).lastIndexOf("out");
  const label = `Resident phone, ${look.style}`;

  return (
    <PhoneFrame
      skin={channel}
      contact="Saklolo"
      status={look.status}
      label={label}
      testId={testId}
      thread={
        <ol
          ref={threadEnd}
          data-testid="phone-thread"
          aria-live="polite"
          className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto px-3 py-3"
        >
          {thread.length === 0 && !sending && (
            <li
              data-testid="phone-hint"
              className="flex flex-col items-center gap-2 rounded-tile bg-surface p-3"
            >
              <Text variant="caption" tone="muted">
                Try a sample message:
              </Text>
              {SAMPLES.map((sample) => (
                <Button
                  key={sample}
                  variant="secondary"
                  size="sm"
                  testId="phone-sample"
                  lang="fil"
                  onClick={() => setDraft(sample)}
                >
                  {sample}
                </Button>
              ))}
            </li>
          )}
          {thread.map((message, index) => (
            <li
              key={`${message.at}-${index}`}
              data-testid="phone-message"
              data-direction={message.direction}
              className="flex flex-col"
            >
              <Bubble
                skin={channel}
                direction={message.direction}
                time={clockTime(message.at)}
                delivered={channel === "telegram" && message.direction === "out"}
                avatar={channel === "messenger" && message.direction === "in" ? "S" : undefined}
                lang={message.direction === "out" ? "fil" : undefined}
              >
                {message.body}
              </Bubble>
              {channel === "sms" && index === lastOut && (
                <span className="self-end pt-1">
                  <Text variant="caption" tone="faint">
                    Delivered
                  </Text>
                </span>
              )}
            </li>
          ))}
          {sending && (
            <li data-testid="phone-sending" className="sk-fade self-end">
              <Text variant="caption" tone="muted">
                Sending…
              </Text>
            </li>
          )}
        </ol>
      }
      composer={
        <>
          {error && (
            <div role="alert" className="flex items-center gap-2 px-3 pt-2">
              <Text variant="caption-bold">
                <span className="inline-flex items-center gap-1">
                  <Icon name="alert" />
                  {error}
                </span>
              </Text>
              <span className="ml-auto">
                <Button
                  variant="ghost"
                  size="sm"
                  testId="phone-retry"
                  disabled={sending}
                  onClick={() => void send()}
                >
                  Retry
                </Button>
              </span>
            </div>
          )}
          <form
            className="flex items-center gap-2 px-3 pt-2"
            onSubmit={(event) => {
              event.preventDefault();
              void send();
            }}
          >
            {look.tools.map((tool) => (
              <span key={tool} aria-hidden>
                <Icon name={tool} size="md" />
              </span>
            ))}
            <label className="sr-only" htmlFor={`${testId}-input`}>
              Message
            </label>
            <div className="min-w-0 flex-1">
              <Input
                id={`${testId}-input`}
                testId="phone-input"
                placeholder={look.placeholder}
                value={draft}
                disabled={sending}
                onChange={(event) => setDraft(event.target.value)}
              />
            </div>
            <Button
              type="submit"
              variant="ghost"
              testId="phone-send"
              aria-label="Send"
              disabled={!draft.trim()}
              loading={sending}
            >
              {!sending && <Icon name="send" />}
            </Button>
          </form>
        </>
      }
    >
      <div className="flex flex-col items-center gap-1">
        <label className="flex items-center gap-2">
          <Text variant="caption" tone="muted">
            Sender
          </Text>
          <Input
            mono
            testId="phone-sender"
            value={sender}
            onChange={(event) => setSender(event.target.value)}
          />
        </label>
      </div>
    </PhoneFrame>
  );
}
