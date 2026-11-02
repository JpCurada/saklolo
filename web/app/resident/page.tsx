import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { AuthGate } from "@/features/auth/AuthGate";
import { ResidentPhones } from "@/features/simulator/ResidentPhones";
import { DEMO_MODE } from "@/lib/demo";

export const metadata: Metadata = { title: "Resident phones · Saklolo" };

export default function ResidentPage() {
  if (!DEMO_MODE) notFound();
  return (
    <AuthGate>
      <ResidentPhones />
    </AuthGate>
  );
}
