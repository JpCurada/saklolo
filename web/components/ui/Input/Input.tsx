import type { InputHTMLAttributes } from "react";

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "className" | "style"> {
  /** For codes and phone numbers. */
  mono?: boolean;
  testId?: string;
}

export function Input({ mono, testId, ...rest }: InputProps) {
  return (
    <input
      {...rest}
      data-testid={testId}
      className={`w-full rounded-(--sk-radius-tile) bg-(--sk-color-input-bg) px-(--sk-space-3) py-(--sk-space-2) text-(length:--sk-text-body-size) text-(--sk-color-input-fg) placeholder:text-(--sk-color-input-placeholder) focus-visible:outline-(length:--sk-stroke-2) focus-visible:outline-(--sk-color-accent) disabled:opacity-50 ${mono ? "font-mono" : ""}`}
    />
  );
}
