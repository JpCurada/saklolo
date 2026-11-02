import type { ReactNode } from "react";

import { Text } from "../Text/Text";

interface PanelProps {
  title: string;
  testId: string;
  /** Controls at the end of the header, such as tabs. */
  actions?: ReactNode;
  children: ReactNode;
}

/** A titled, scrolling region of the dashboard. */
export function Panel({ title, testId, actions, children }: PanelProps) {
  return (
    <section
      data-testid={testId}
      aria-label={title}
      className="flex min-h-0 flex-col rounded-(--sk-radius-tile) bg-(--sk-color-surface)"
    >
      <header className="flex min-w-0 flex-wrap items-center justify-between gap-(--sk-space-2) px-(--sk-space-4) py-(--sk-space-3)">
        <Text as="h2" variant="body-bold">
          {title}
        </Text>
        {actions}
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
    </section>
  );
}
