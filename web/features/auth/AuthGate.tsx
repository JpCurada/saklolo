"use client";

import Image from "next/image";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { Button, Text } from "@/components/ui";
import { onUnauthorized, setAccessToken } from "@/lib/api/client";
import {
  AUTH_ENABLED,
  forgetSession,
  loadSession,
  onSessionChange,
  signIn,
  signOut,
  type Session,
} from "@/lib/auth";

interface SignedIn {
  username: string;
  signOut: () => Promise<void>;
}

const SessionContext = createContext<SignedIn | null>(null);

/** The signed-in dispatcher, or null when sign-in is off (a local API). */
export function useSignedIn(): SignedIn | null {
  return useContext(SessionContext);
}

/** Shows its children only to a signed-in dispatcher when Cognito is configured. */
export function AuthGate({ children }: { children: ReactNode }) {
  if (!AUTH_ENABLED) return children;
  return <CognitoGate>{children}</CognitoGate>;
}

function CognitoGate({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null | undefined>(undefined);

  useEffect(() => {
    let active = true;
    const apply = (next: Session | null) => {
      setAccessToken(next?.accessToken ?? null);
      if (active) setSession(next);
    };
    void loadSession().then(apply, () => apply(null));
    const stopWatching = onSessionChange(apply);
    const stopListening = onUnauthorized(() => void forgetSession().then(() => apply(null)));
    return () => {
      active = false;
      stopWatching();
      stopListening();
    };
  }, []);

  if (session === undefined) return null;
  if (session === null) return <SignInScreen />;
  return (
    <SessionContext.Provider value={{ username: session.username, signOut }}>
      {children}
    </SessionContext.Provider>
  );
}

function SignInScreen() {
  const [pending, setPending] = useState(false);
  return (
    <main
      data-testid="sign-in-screen"
      className="flex min-h-screen flex-col items-center justify-center gap-4 p-6 text-center"
    >
      <Image src="/assets/logo-mark.svg" width={64} height={64} alt="" unoptimized />
      <Text as="h1" variant="title-m">
        Saklolo dispatch
      </Text>
      <Text as="p" tone="muted">
        Sign in to see the queue. Accounts are by invitation only.
      </Text>
      <Button
        testId="sign-in"
        loading={pending}
        onClick={() => {
          setPending(true);
          void signIn(window.location.pathname);
        }}
      >
        Sign in
      </Button>
    </main>
  );
}
