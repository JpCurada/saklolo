import type { ReactNode } from "react";

interface PanelProps {
  title: string;
  testId: string;
  actions?: ReactNode;
  children: ReactNode;
}

export function Panel({ title, testId, actions, children }: PanelProps) {
  return (
    <section
      data-testid={testId}
      aria-label={title}
      className="flex min-h-0 flex-col rounded-lg border border-slate-800 bg-slate-900/70"
    >
      <header className="flex items-center justify-between border-b border-slate-800 px-4 py-2.5">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">{title}</h2>
        {actions}
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
    </section>
  );
}
