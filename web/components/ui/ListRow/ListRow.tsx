import type { ReactNode } from "react";

interface ListRowProps {
  testId: string;
  /** Small facts above the content. */
  meta: ReactNode;
  /** Pinned to the end of the meta line, such as a priority. */
  trailing?: ReactNode;
  /** Makes the row a button. */
  onSelect?: () => void;
  selected?: boolean;
  caseId?: string;
  /** Slide in, for a row that just arrived. */
  enter?: boolean;
  children: ReactNode;
}

const PADDING = "px-(--sk-space-4) py-(--sk-space-2)";

/** One row of a list, separated by space rather than a line. */
export function ListRow({
  testId,
  meta,
  trailing,
  onSelect,
  selected = false,
  caseId,
  enter,
  children,
}: ListRowProps) {
  const body = (
    <>
      <div className="flex min-w-0 flex-wrap items-center gap-(--sk-space-2)">
        {meta}
        {trailing && <span className="ml-auto">{trailing}</span>}
      </div>
      {children}
    </>
  );
  const entering = enter ? "sk-enter" : "";
  if (!onSelect) {
    return (
      <li data-testid={testId} className={`${PADDING} ${entering}`}>
        {body}
      </li>
    );
  }
  return (
    <li className={entering}>
      <button
        type="button"
        data-testid={testId}
        data-case-id={caseId}
        aria-pressed={selected}
        onClick={onSelect}
        className={`relative block w-full text-left transition-colors duration-(--sk-motion-fast) focus-visible:outline-(length:--sk-stroke-2) focus-visible:-outline-offset-2 focus-visible:outline-(--sk-color-accent) ${PADDING} ${
          selected ? "bg-(--sk-color-accent-tint)" : "hover:bg-(--sk-color-canvas)"
        }`}
      >
        {body}
      </button>
    </li>
  );
}
