// The one typed client for the Saklolo demo API (api/src/saklolo/handlers/demo_api.py).
import type {
  CaseView,
  MessageIn,
  MessageRecord,
  OutboundMessage,
  Priority,
  ReceiveResult,
  ReplayIn,
  ReplayStatus,
} from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "content-type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, detail || response.statusText);
  }
  return (await response.json()) as T;
}

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body ?? {}) });

export const api = {
  cases: (includeClosed = false) => request<CaseView[]>(`/cases?include_closed=${includeClosed}`),
  messages: () => request<MessageRecord[]>("/messages"),
  outbox: (recipient: string) =>
    request<OutboundMessage[]>(`/outbox?recipient=${encodeURIComponent(recipient)}`),
  send: (message: MessageIn) => post<ReceiveResult>("/messages", message),
  assign: (caseId: string, team: string) => post<CaseView>(`/cases/${caseId}/assign`, { team }),
  override: (caseId: string, priority: Priority, reason: string) =>
    post<CaseView>(`/cases/${caseId}/override`, { priority, reason }),
  confirmSafe: (caseId: string) => post<CaseView>(`/cases/${caseId}/confirm-safe`),
  replay: () => request<ReplayStatus>("/replay"),
  startReplay: (settings: ReplayIn) => post<ReplayStatus>("/replay", settings),
  stopReplay: () => request<ReplayStatus>("/replay", { method: "DELETE" }),
};
