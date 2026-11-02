"use client";

import { useCallback, useState } from "react";

import { api } from "@/lib/api/client";
import { usePolling } from "@/lib/usePolling";

import { CaseDetail } from "../case-detail/CaseDetail";
import { CaseMap } from "../case-detail/CaseMap";
import { MessageFeed } from "../feed/MessageFeed";
import { QueuePanel } from "../queue/QueuePanel";
import { ReplayControls } from "../replay/ReplayControls";
import { PhoneSimulator } from "../simulator/PhoneSimulator";
import { StatsBar } from "./StatsBar";

const fetchCases = () => api.cases();

/** 1920×1080 dispatcher screen: queue | case + map | phone + incoming feed. */
export function Dashboard() {
  const cases = usePolling(fetchCases);
  const messages = usePolling(api.messages);
  const [chosenId, setChosenId] = useState<string>();
  const list = cases.data ?? [];
  const selectedId = chosenId ?? list[0]?.case_id;
  const selected = list.find((item) => item.case_id === selectedId);

  const refreshAll = useCallback(() => {
    void cases.refresh();
    void messages.refresh();
  }, [cases, messages]);

  return (
    <div className="flex h-screen flex-col gap-3 bg-slate-950 p-3 text-slate-100">
      <header
        data-testid="app-header"
        className="flex items-center gap-4 rounded-lg border border-slate-800 bg-slate-900/70 px-4 py-2"
      >
        <h1 data-testid="logo" className="text-xl font-black tracking-tight">
          SAKLOLO <span className="font-normal text-slate-400">· Marikina dispatch</span>
        </h1>
        <StatsBar cases={list} />
        <div className="ml-auto">
          <ReplayControls onTick={refreshAll} />
        </div>
      </header>

      {cases.error && (
        <p
          role="alert"
          data-testid="api-error"
          className="rounded bg-red-950 px-3 py-2 text-sm text-red-300"
        >
          Can&apos;t reach the Saklolo API ({cases.error}). Start it with <code>make demo</code>.
        </p>
      )}

      <main className="grid min-h-0 flex-1 grid-cols-[30fr_42fr_28fr] gap-3">
        <QueuePanel cases={list} selectedId={selectedId} onSelect={setChosenId} />
        <div className="grid min-h-0 grid-rows-[3fr_2fr] gap-3">
          <CaseDetail item={selected} onChanged={refreshAll} />
          <section
            aria-label="Map of open cases"
            className="min-h-0 overflow-hidden rounded-lg border border-slate-800"
          >
            <CaseMap cases={list} selectedId={selectedId} onSelect={setChosenId} />
          </section>
        </div>
        <div className="grid min-h-0 grid-rows-[1fr_1fr] gap-3">
          <PhoneSimulator onSent={refreshAll} />
          <MessageFeed messages={messages.data ?? []} />
        </div>
      </main>
    </div>
  );
}
