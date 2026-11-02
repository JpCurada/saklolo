"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Text } from "@/components/ui";
import { AUTH_ENABLED, completeSignIn } from "@/lib/auth";

/** Cognito's hosted page returns here with a code; finish sign-in and go back. */
export default function AuthCallback() {
  const [failed, setFailed] = useState(!AUTH_ENABLED);

  useEffect(() => {
    if (!AUTH_ENABLED) return;
    completeSignIn().then(
      (returnTo) => window.location.replace(returnTo),
      () => setFailed(true),
    );
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-3 p-6 text-center">
      <Text as="p" tone="muted">
        {failed ? "Sign-in didn't complete." : "Signing you in…"}
      </Text>
      {failed && (
        <Link href="/dispatch" data-testid="back-home">
          <Text variant="body-bold">Back to the dashboard</Text>
        </Link>
      )}
    </main>
  );
}
