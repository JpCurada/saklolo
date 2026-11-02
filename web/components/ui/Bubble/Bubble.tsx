import type { ReactNode } from "react";

import { Icon } from "../Icon/Icon";

export type PhoneSkin = "sms" | "telegram" | "messenger";

const SKIN: Record<PhoneSkin, { out: string; in: string; shape: { out: string; in: string } }> = {
  sms: {
    out: "bg-(--sk-color-phone-sms-out) text-(--sk-color-phone-sms-out-fg)",
    in: "bg-(--sk-color-phone-sms-in) text-(--sk-color-phone-sms-in-fg)",
    shape: { out: "rounded-(--sk-radius-tile)", in: "rounded-(--sk-radius-tile)" },
  },
  // Telegram-style: a small tail corner on the sender's side.
  telegram: {
    out: "bg-(--sk-color-phone-telegram-out) text-(--sk-color-phone-telegram-out-fg)",
    in: "bg-(--sk-color-phone-telegram-in) text-(--sk-color-phone-telegram-in-fg)",
    shape: {
      out: "rounded-(--sk-space-3) rounded-br-(--sk-space-1)",
      in: "rounded-(--sk-space-3) rounded-bl-(--sk-space-1)",
    },
  },
  messenger: {
    out: "bg-(--sk-color-phone-messenger-out) text-(--sk-color-phone-messenger-out-fg)",
    in: "bg-(--sk-color-phone-messenger-in) text-(--sk-color-phone-messenger-in-fg)",
    shape: { out: "rounded-(--sk-space-5)", in: "rounded-(--sk-space-5)" },
  },
};

interface BubbleProps {
  /** `out` is what the resident sent; `in` is what they received. */
  direction: "in" | "out";
  skin: PhoneSkin;
  /** Shown inside the bubble, like chat apps do. */
  time?: string;
  /** Double ticks after the time, for a delivered message. */
  delivered?: boolean;
  /** The contact's initial beside a received message. */
  avatar?: string;
  testId?: string;
  lang?: string;
  children: ReactNode;
}

/** One message on a simulated resident phone. */
export function Bubble({
  direction,
  skin,
  time,
  delivered,
  avatar,
  testId,
  lang,
  children,
}: BubbleProps) {
  const style = SKIN[skin];
  const side = direction === "out" ? "self-end" : "self-start";
  const bubble = (
    <p
      data-testid={testId}
      lang={lang}
      className={`sk-enter max-w-5/6 px-(--sk-space-3) py-(--sk-space-2) text-(length:--sk-text-body-size) leading-(--sk-text-body-line-height) ${avatar ? "" : side} ${style[direction]} ${style.shape[direction]}`}
    >
      {children}
      {time && (
        <span className="ml-(--sk-space-2) inline-flex items-center gap-(--sk-space-1) align-bottom text-(length:--sk-text-caption-size) opacity-70">
          {time}
          {delivered && <Icon name="check-double" size="sm" />}
        </span>
      )}
    </p>
  );
  if (!avatar) return bubble;
  return (
    <div className={`flex items-end gap-(--sk-space-2) ${side}`}>
      <span
        aria-hidden
        className="flex size-(--sk-space-6) shrink-0 items-center justify-center rounded-(--sk-radius-pill) bg-(--sk-color-phone-messenger-accent) text-(length:--sk-text-caption-size) text-(--sk-color-phone-messenger-out-fg)"
      >
        {avatar}
      </span>
      {bubble}
    </div>
  );
}
