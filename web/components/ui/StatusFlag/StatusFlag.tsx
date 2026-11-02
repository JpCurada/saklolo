import type { ReactNode } from "react";

interface StatusFlagProps {
  /** The value for `data-badge`. */
  flag: string;
  icon?: ReactNode;
  children: ReactNode;
}

/** A case flag, such as "Corroborated". Neutral, because color means priority (R5). */
export function StatusFlag({ flag, icon, children }: StatusFlagProps) {
  return (
    <li
      data-testid="badge"
      data-badge={flag}
      className="inline-flex items-center gap-(--sk-space-1) rounded-(--sk-radius-pill) bg-(--sk-color-canvas) px-(--sk-space-2) text-(length:--sk-text-caption-bold-size) font-(weight:--sk-text-caption-bold-weight) leading-(--sk-text-caption-bold-line-height) text-(--sk-color-ink-muted)"
    >
      {icon}
      {children}
    </li>
  );
}

/** The list a row's `StatusFlag`s sit in. */
export function StatusFlagList({ children }: { children: ReactNode }) {
  return (
    <ul data-testid="case-badges" className="flex flex-wrap gap-(--sk-space-1)">
      {children}
    </ul>
  );
}
