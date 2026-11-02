import type { ReactNode } from "react";

const TONE = {
  critical: "bg-(--sk-color-status-critical) text-(--sk-color-ink-on-status)",
  high: "bg-(--sk-color-status-high) text-(--sk-color-ink-on-status)",
  moderate: "bg-(--sk-color-status-moderate) text-(--sk-color-ink-on-status)",
  info: "bg-(--sk-color-status-info) text-(--sk-color-ink-on-status)",
  none: "bg-(--sk-color-canvas) text-(--sk-color-ink-muted)",
};

export type BadgeTone = keyof typeof TONE;

interface BadgeProps {
  tone: BadgeTone;
  /** Pulse for an unassigned P1 (R21). */
  urgent?: boolean;
  testId?: string;
  priority?: string;
  children: ReactNode;
}

/** A filled priority pill. Always has text, so color is never the only signal. */
export function Badge({ tone, urgent, testId, priority, children }: BadgeProps) {
  return (
    <span
      data-testid={testId}
      data-priority={priority}
      className={`rounded-(--sk-radius-pill) px-(--sk-space-2) text-(length:--sk-text-caption-bold-size) font-(weight:--sk-text-caption-bold-weight) leading-(--sk-text-caption-bold-line-height) ${TONE[tone]} ${urgent ? "sk-pulse-critical" : ""}`}
    >
      {children}
    </span>
  );
}
