import type { ReactNode } from "react";

import { Icon } from "../Icon/Icon";
import { Text } from "../Text/Text";

interface DisclosureProps {
  title: string;
  /** Shown after the title, such as a count or a one-line summary. */
  meta?: ReactNode;
  /** Open on first render. The dispatcher can still fold it away. */
  defaultOpen?: boolean;
  testId?: string;
  children: ReactNode;
}

/** A section that folds to its header, so a long case reads top-down. Native <details>. */
export function Disclosure({
  title,
  meta,
  defaultOpen = false,
  testId,
  children,
}: DisclosureProps) {
  return (
    <details data-testid={testId} open={defaultOpen} className="group/disclosure">
      <summary className="flex min-h-(--sk-space-10) cursor-pointer list-none items-center gap-(--sk-space-2) rounded-(--sk-radius-tile) px-(--sk-space-2) py-(--sk-space-1) hover:bg-(--sk-color-canvas) focus-visible:outline-(length:--sk-stroke-2) focus-visible:outline-(--sk-color-accent)">
        <span className="shrink-0 transition-transform duration-(--sk-motion-fast) group-open/disclosure:rotate-90 motion-reduce:transition-none">
          <Icon name="chevron-right" />
        </span>
        <span className="flex min-w-0 flex-1 flex-wrap items-center gap-x-(--sk-space-1)">
          <Text variant="body-bold">{title}</Text>
          {meta && (
            <Text variant="caption" tone="muted">
              {meta}
            </Text>
          )}
        </span>
      </summary>
      <div className="mt-(--sk-space-2)">{children}</div>
    </details>
  );
}
