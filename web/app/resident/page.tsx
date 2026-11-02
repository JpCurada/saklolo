import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { ResidentPhones } from "@/features/simulator/ResidentPhones";
import { DEMO_MODE } from "@/lib/demo";

export const metadata: Metadata = { title: "Resident phones · Saklolo" };

export default function ResidentPage() {
  if (!DEMO_MODE) notFound();
  return <ResidentPhones />;
}
