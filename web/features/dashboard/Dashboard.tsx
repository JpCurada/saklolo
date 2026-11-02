"use client";

import Image from "next/image";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import { Text, Toast, type ToastItem } from "@/components/ui";
import { api } from "@/lib/api/client";
import { DEMO_MODE } from "@/lib/demo";
import { usePolling } from "@/lib/usePolling";

import { CaseDetail } from "../case-detail/CaseDetail";
import { CaseMap } from "../case-detail/CaseMap";
import { DispatcherPicker } from "../dispatcher/DispatcherPicker";
import { useDispatcher } from "../dispatcher/useDispatcher";
import { MessageFeed } from "../feed/MessageFeed";
import { QueuePanel } from "../queue/QueuePanel";
import { isUnassignedCritical } from "../queue/urgency";
import { ReplayControls } from "../replay/ReplayControls";
import { BootPanel } from "./BootPanel";
import { StatsBar } from "./StatsBar";

const APP_TITLE = "Saklolo dispatch";
const TOAST_MS = 6000;

const fetchCases = () => api.cases();

/** 1920×1080 dispatcher screen: queue | case + map | phone + incoming feed. */
export function Dashboard() {
  const cases = usePolling(fetchCases);
  const messages = usePolling(api.messages);
  const [chosenId, setChosenId] = useState<string>();
  const [dispatcher, setDispatcher] = useDispatcher();
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const toastCount = useRef(0);
  const list = cases.data ?? [];
  const selectedId = chosenId ?? list[0]?.case_id;
  const selected = list.find((item) => item.case_id === selectedId);
  const booting = cases.data === undefined && !cases.error;
  const untaken = list.filter(isUnassignedCritical).length;

  const refreshAll = useCallback(() => {
    void cases.refresh();
    void messages.refresh();
  }, [cases, messages]);

  const dismissToast = useCallback((id: string) => {
    setToasts((shown) => shown.filter((toast) => toast.id !== id));
  }, []);

  // The list drops a closed case, so this is the record that a person closed it.
  const confirmClosed = useCallback(
    (by: string) => {
      setChosenId(undefined);
      toastCount.current += 1;
      const id = String(toastCount.current);
      setToasts((shown) => [...shown, { id, message: `Case closed by ${by}.` }]);
      setTimeout(() => dismissToast(id), TOAST_MS);
    },
    [dismissToast],
  );

  // Visible from another tab, where a dispatcher can't see the queue.
  useEffect(() => {
    document.title = untaken > 0 ? `(${untaken} P1) ${APP_TITLE}` : APP_TITLE;
  }, [untaken]);

  return (
    <div className="sk-shell">
      <header data-testid="app-header" className="sk-header">
        <div data-testid="logo" className="sk-brand">
          <Image src="/assets/logo-mark.svg" width={32} height={32} alt="" unoptimized />
          <Text as="h1" variant="title-m">
            Saklolo{" "}
            <Text variant="body" tone="muted">
              · Marikina dispatch
            </Text>
          </Text>
        </div>
        {cases.data && <StatsBar cases={cases.data} />}
        <div className="sk-header-actions">
          <DispatcherPicker name={dispatcher} onChange={setDispatcher} />
          {DEMO_MODE && (
            <>
              <ReplayControls onTick={refreshAll} />
              <Link href="/resident" target="_blank" data-testid="open-resident">
                <Text variant="body-bold">Resident phones</Text>
              </Link>
            </>
          )}
        </div>
      </header>

      <main className="sk-board">
        <QueuePanel
          cases={list}
          loading={booting}
          error={cases.error}
          selectedId={selectedId}
          onSelect={setChosenId}
        />
        {booting ? (
          <BootPanel />
        ) : (
          <>
            <div className="sk-column-center">
              <CaseDetail
                item={selected}
                dispatcher={dispatcher}
                onChanged={refreshAll}
                onClosed={confirmClosed}
              />
              <section aria-label="Map of open cases" className="sk-map-frame">
                <CaseMap cases={list} selectedId={selectedId} onSelect={setChosenId} />
              </section>
            </div>
            <div className="sk-column-side">
              <MessageFeed messages={messages.data ?? []} loading={!messages.data} />
            </div>
          </>
        )}
      </main>
      <Toast toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
