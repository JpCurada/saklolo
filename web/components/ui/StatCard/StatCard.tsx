interface StatCardProps {
  label: string;
  value: number;
  testId: string;
  /** A single row for the header, instead of a stacked tile. */
  compact?: boolean;
  /** Use the P1 color: for a count of P1 cases only (R5). */
  critical?: boolean;
}

/** A number first, its label second. Goes inside a `<dl>`. */
export function StatCard({ label, value, testId, compact, critical }: StatCardProps) {
  const tone = critical ? "text-(--sk-color-status-critical)" : "text-(--sk-color-ink)";
  return (
    <div
      data-testid={testId}
      className={
        compact
          ? "flex items-baseline gap-(--sk-space-1)"
          : "flex flex-col rounded-(--sk-radius-tile) bg-(--sk-color-canvas) p-(--sk-space-3)"
      }
    >
      {/* Keyed, so a new value replays the pop and the change gets noticed. */}
      <dd
        key={value}
        className={`sk-pop text-(length:--sk-text-title-m-size) font-(weight:--sk-text-title-m-weight) tabular-nums ${tone}`}
      >
        {value}
      </dd>
      <dt className="text-(length:--sk-text-caption-size) text-(--sk-color-ink-muted)">{label}</dt>
    </div>
  );
}
