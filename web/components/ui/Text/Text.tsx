import type { ReactNode } from "react";

const VARIANT = {
  display:
    "text-(length:--sk-text-display-size) font-(weight:--sk-text-display-weight) leading-(--sk-text-display-line-height) tracking-(--sk-text-display-tracking)",
  "title-l":
    "text-(length:--sk-text-title-l-size) font-(weight:--sk-text-title-l-weight) leading-(--sk-text-title-l-line-height) tracking-(--sk-text-title-l-tracking)",
  "title-m":
    "text-(length:--sk-text-title-m-size) font-(weight:--sk-text-title-m-weight) leading-(--sk-text-title-m-line-height) tracking-(--sk-text-title-m-tracking)",
  "body-bold":
    "text-(length:--sk-text-body-bold-size) font-(weight:--sk-text-body-bold-weight) leading-(--sk-text-body-bold-line-height)",
  body: "text-(length:--sk-text-body-size) font-(weight:--sk-text-body-weight) leading-(--sk-text-body-line-height)",
  "caption-bold":
    "text-(length:--sk-text-caption-bold-size) font-(weight:--sk-text-caption-bold-weight) leading-(--sk-text-caption-bold-line-height)",
  caption:
    "text-(length:--sk-text-caption-size) font-(weight:--sk-text-caption-weight) leading-(--sk-text-caption-line-height)",
};

const TONE = {
  ink: "text-(--sk-color-ink)",
  muted: "text-(--sk-color-ink-muted)",
  faint: "text-(--sk-color-ink-faint)",
};

interface TextProps {
  as?: "span" | "p" | "h1" | "h2" | "h3";
  variant?: keyof typeof VARIANT;
  tone?: keyof typeof TONE;
  /** Clamp to two lines, for rows of untrusted-length text. */
  clamp?: boolean;
  lang?: string;
  children: ReactNode;
}

/** Every piece of text on the type scale. */
export function Text({
  as: Tag = "span",
  variant = "body",
  tone = "ink",
  clamp,
  lang,
  children,
}: TextProps) {
  const classes = [VARIANT[variant], TONE[tone], clamp && "line-clamp-2"];
  return (
    <Tag lang={lang} className={classes.filter(Boolean).join(" ")}>
      {children}
    </Tag>
  );
}
