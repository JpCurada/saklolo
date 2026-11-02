import type { Metadata } from "next";

import { AuthGate } from "@/features/auth/AuthGate";
import { Dashboard } from "@/features/dashboard/Dashboard";

export const metadata: Metadata = { title: "Saklolo dispatch" };

export default function DispatchPage() {
  return (
    <AuthGate>
      <Dashboard />
    </AuthGate>
  );
}
