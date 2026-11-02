"use client";

import { UserManager, WebStorageStateStore, type User } from "oidc-client-ts";

/**
 * Dispatcher sign-in with Amazon Cognito: authorization code with PKCE through the hosted
 * page. On only when the build sets the three NEXT_PUBLIC_COGNITO_* values; without them
 * the dashboard runs open against a local API.
 */
const AUTHORITY = process.env.NEXT_PUBLIC_COGNITO_AUTHORITY ?? "";
const CLIENT_ID = process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID ?? "";
const DOMAIN = (process.env.NEXT_PUBLIC_COGNITO_DOMAIN ?? "").replace(/\/+$/, "");

export const AUTH_ENABLED = Boolean(AUTHORITY && CLIENT_ID && DOMAIN);

export interface Session {
  username: string;
  accessToken: string;
}

let manager: UserManager | null = null;

function users(): UserManager {
  manager ??= new UserManager({
    authority: AUTHORITY,
    client_id: CLIENT_ID,
    redirect_uri: `${window.location.origin}/auth/callback`,
    post_logout_redirect_uri: `${window.location.origin}/`,
    response_type: "code",
    scope: "openid email profile",
    // Session storage: closing the tab signs the dispatcher out of this browser.
    userStore: new WebStorageStateStore({ store: window.sessionStorage }),
    automaticSilentRenew: true,
  });
  return manager;
}

function toSession(user: User | null): Session | null {
  if (user === null || user.expired) return null;
  const name = user.profile["cognito:username"];
  return {
    username: typeof name === "string" && name ? name : user.profile.sub,
    accessToken: user.access_token,
  };
}

export async function loadSession(): Promise<Session | null> {
  return toSession(await users().getUser());
}

/** Session changes made outside a page action: token renewal and expiry. */
export function onSessionChange(listener: (session: Session | null) => void): () => void {
  const loaded = (user: User) => listener(toSession(user));
  const gone = () => listener(null);
  const events = users().events;
  events.addUserLoaded(loaded);
  events.addUserUnloaded(gone);
  events.addAccessTokenExpired(gone);
  return () => {
    events.removeUserLoaded(loaded);
    events.removeUserUnloaded(gone);
    events.removeAccessTokenExpired(gone);
  };
}

/** Only same-site paths are followed after sign-in. */
function safePath(value: unknown): string {
  if (typeof value !== "string" || !value.startsWith("/") || value.startsWith("//")) return "/";
  return value.startsWith("/auth/") ? "/" : value;
}

export async function signIn(returnTo: string): Promise<void> {
  await users().signinRedirect({ state: { returnTo: safePath(returnTo) } });
}

/** Finishes sign-in on /auth/callback and returns the page to go back to. */
export async function completeSignIn(): Promise<string> {
  const user = await users().signinRedirectCallback();
  const state = user.state as { returnTo?: unknown } | undefined;
  return safePath(state?.returnTo);
}

/** Clears this browser's session, then signs out of the hosted page too. */
export async function signOut(): Promise<void> {
  await users().removeUser();
  const query = new URLSearchParams({
    client_id: CLIENT_ID,
    logout_uri: `${window.location.origin}/`,
  });
  // Cognito's own domain, outside the dashboard.
  window.location.replace(`${DOMAIN}/logout?${query.toString()}`);
}

/** The API refused the token: forget it locally and ask again. */
export async function forgetSession(): Promise<void> {
  await users().removeUser();
}
