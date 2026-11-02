import type { ReactNode } from "react";

import { Text } from "../Text/Text";

interface TileProps {
  label: string;
  testId?: string;
  children: ReactNode;
}

/** One labelled fact inside a panel. */
export function Tile({ label, testId, children }: TileProps) {
  return (
    <div
      data-testid={testId}
      className="flex flex-col rounded-(--sk-radius-tile) bg-(--sk-color-canvas) px-(--sk-space-3) py-(--sk-space-2)"
    >
      <Text variant="caption" tone="muted">
        {label}
      </Text>
      <Text variant="body-bold">{children}</Text>
    </div>
  );
}
