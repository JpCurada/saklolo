import type { SelectHTMLAttributes } from "react";

import { Icon } from "../Icon/Icon";

interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "className" | "style"> {
  testId?: string;
}

export function Select({ testId, children, ...rest }: SelectProps) {
  return (
    <span className="relative inline-flex min-w-0">
      <select
        {...rest}
        data-testid={testId}
        className="min-w-0 cursor-pointer appearance-none rounded-(--sk-radius-tile) bg-(--sk-color-input-bg) py-(--sk-space-2) pr-(--sk-space-10) pl-(--sk-space-3) text-(length:--sk-text-body-size) text-(--sk-color-input-fg) focus-visible:outline-(length:--sk-stroke-2) focus-visible:outline-(--sk-color-accent) disabled:cursor-not-allowed disabled:opacity-50"
      >
        {children}
      </select>
      <span
        aria-hidden
        className="pointer-events-none absolute top-1/2 right-(--sk-space-3) -translate-y-1/2 rotate-90 text-(--sk-color-ink-muted)"
      >
        <Icon name="chevron-right" />
      </span>
    </span>
  );
}
