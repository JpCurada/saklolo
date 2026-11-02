import type { ButtonHTMLAttributes, Ref } from "react";

const VARIANT = {
  primary: "bg-(--sk-color-button-primary-bg) text-(--sk-color-button-primary-fg)",
  secondary: "bg-(--sk-color-button-secondary-bg) text-(--sk-color-button-secondary-fg)",
  danger: "bg-(--sk-color-button-danger-bg) text-(--sk-color-button-danger-fg)",
  ghost: "text-(--sk-color-ink-muted) hover:bg-(--sk-color-canvas)",
};

const SIZE = {
  sm: "px-(--sk-space-3) py-(--sk-space-1) text-(length:--sk-text-caption-bold-size) font-(weight:--sk-text-caption-bold-weight)",
  md: "px-(--sk-space-4) py-(--sk-space-2) text-(length:--sk-text-body-bold-size) font-(weight:--sk-text-body-bold-weight)",
};

interface ButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className" | "style"> {
  variant?: keyof typeof VARIANT;
  size?: keyof typeof SIZE;
  /** Shows a spinner and blocks repeat presses. */
  loading?: boolean;
  /** Fill the width of the container. */
  block?: boolean;
  testId?: string;
  ref?: Ref<HTMLButtonElement>;
}

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  block,
  testId,
  disabled,
  type = "button",
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      {...rest}
      type={type}
      data-testid={testId}
      disabled={disabled || loading}
      aria-busy={loading}
      className={`inline-flex shrink-0 items-center whitespace-nowrap justify-center gap-(--sk-space-2) rounded-(--sk-radius-pill) transition-opacity duration-(--sk-motion-fast) focus-visible:outline-(length:--sk-stroke-2) focus-visible:outline-offset-(--sk-stroke-2) focus-visible:outline-(--sk-color-accent) disabled:cursor-not-allowed disabled:opacity-50 ${VARIANT[variant]} ${SIZE[size]} ${block ? "w-full" : ""}`}
    >
      {loading && (
        <span
          aria-hidden
          className="sk-spin size-(--sk-space-3) rounded-(--sk-radius-pill) border-(length:--sk-stroke-2) border-current border-t-transparent"
        />
      )}
      {children}
    </button>
  );
}
