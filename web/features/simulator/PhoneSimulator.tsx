"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { Panel } from "@/components/Panel";
import { api } from "@/lib/api/client";
import { clockTime } from "@/lib/format";
import { usePolling } from "@/lib/usePolling";

// A clearly fake number (dataset-spec section 9), outside the dataset's range.
const DEFAULT_SENDER = "+639000000901";

interface ThreadMessage {
  direction: "out" | "in";
  body: string;
  at: string;
}

/** A simulated phone: sends to the same intake as SMS, shows what the resident gets back. */
export function PhoneSimulator({ onSent }: { onSent: () => void }) {
  const [sender, setSender] = useState(DEFAULT_SENDER);
  const [draft, setDraft] = useState("");
  const [sent, setSent] = useState<ThreadMessage[]>([]);
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
  }, [thread.length]);

  async function send() {
    const text = draft.trim();
    if (!text) return;
    try {
      const result = await api.send({ sender, text, channel: "sms" });
      setSent((previous) => [
        ...previous,
        { direction: "out", body: text, at: result.record.message.received_at },
      ]);
      setDraft("");
      setError(undefined);
      await replies.refresh();
      onSent();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    }
  }

  return (
    <Panel title="Phone simulator" testId="phone-simulator">
      <div className="flex h-full flex-col">
        <label className="flex items-center gap-2 border-b border-slate-800 px-4 py-2 text-xs text-slate-400">
          Sender
          <input
            data-testid="phone-sender"
            value={sender}
            onChange={(event) => setSender(event.target.value)}
            className="flex-1 rounded border border-slate-700 bg-slate-950 px-2 py-1 font-mono text-xs text-slate-200"
          />
        </label>
        <ol
          ref={threadEnd}
          data-testid="phone-thread"
          className="min-h-0 flex-1 space-y-2 overflow-y-auto px-4 py-3"
        >
          {thread.map((message, index) => (
            <li
              key={`${message.at}-${index}`}
              data-testid="phone-message"
              data-direction={message.direction}
              className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm ${
                message.direction === "out"
                  ? "ml-auto bg-sky-600 text-white"
                  : "bg-slate-800 text-slate-100"
              }`}
            >
              <p>{message.body}</p>
              <p className="mt-1 text-[10px] opacity-70">{clockTime(message.at)}</p>
            </li>
          ))}
        </ol>
        <form
          className="flex gap-2 border-t border-slate-800 p-3"
          onSubmit={(event) => {
            event.preventDefault();
            void send();
          }}
        >
          <label className="sr-only" htmlFor="phone-input">
            Message
          </label>
          <input
            id="phone-input"
            data-testid="phone-input"
            placeholder="Type a message (Taglish is fine)"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            className="flex-1 rounded-full border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
          <button
            type="submit"
            data-testid="phone-send"
            disabled={!draft.trim()}
            className="rounded-full bg-sky-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-40"
          >
            Send
          </button>
        </form>
        {error && (
          <p role="alert" className="px-4 pb-2 text-xs text-red-400">
            {error}
          </p>
        )}
      </div>
    </Panel>
  );
}
