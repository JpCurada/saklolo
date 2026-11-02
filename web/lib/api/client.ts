// The one typed client for the Saklolo demo API (api/src/saklolo/handlers/demo_api.py).
import type {
  CaseView,
  MessageIn,
  MessageRecord,
  OutboundMessage,
  Priority,
  ReceiveAck,
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

// Set by the sign-in gate (features/auth); null on an open local API.
let accessToken: string | null = null;
const unauthorized = new Set<() => void>();

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

/** Called when the API refuses the token, so the dashboard can ask to sign in again. */
export function onUnauthorized(listener: () => void): () => void {
  unauthorized.add(listener);
  return () => unauthorized.delete(listener);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const auth: Record<string, string> = accessToken
    ? { authorization: `Bearer ${accessToken}` }
    : {};
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "content-type": "application/json", ...auth, ...init?.headers },
  });
  if (response.status === 401) unauthorized.forEach((listener) => listener());
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
  send: (message: MessageIn) => post<ReceiveAck>("/messages", message),
  // Every decision names the dispatcher who made it; the API records it in the case history.
  assign: (caseId: string, team: string, dispatcher: string) =>
    post<CaseView>(`/cases/${caseId}/assign`, { team, dispatcher }),
  override: (caseId: string, priority: Priority, reason: string, dispatcher: string) =>
    post<CaseView>(`/cases/${caseId}/override`, { priority, reason, dispatcher }),
  confirmSafe: (caseId: string, dispatcher: string) =>
    post<CaseView>(`/cases/${caseId}/confirm-safe`, { dispatcher }),
  replay: () => request<ReplayStatus>("/replay"),
  startReplay: (settings: ReplayIn) => post<ReplayStatus>("/replay", settings),
  stopReplay: () => request<ReplayStatus>("/replay", { method: "DELETE" }),
};
