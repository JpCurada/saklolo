import type { SelectHTMLAttributes } from "react";

interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "className" | "style"> {
  testId?: string;
}

export function Select({ testId, children, ...rest }: SelectProps) {
  return (
    <select
      {...rest}
      data-testid={testId}
      className="rounded-(--sk-radius-tile) bg-(--sk-color-input-bg) px-(--sk-space-3) py-(--sk-space-2) text-(length:--sk-text-body-size) text-(--sk-color-input-fg) focus-visible:outline-(length:--sk-stroke-2) focus-visible:outline-(--sk-color-accent) disabled:opacity-50"
    >
      {children}
    </select>
  );
}
