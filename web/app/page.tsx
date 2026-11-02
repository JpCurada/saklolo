import type { Metadata } from "next";

import { Landing } from "@/features/landing/Landing";
import "./landing.css";

export const metadata: Metadata = {
  title: "Saklolo · Typhoon rescue triage",
  description:
    "Rescue requests sent by chat during a typhoon, read and ranked by Strands agents, decided by a human dispatcher.",
};

export default function Home() {
  return <Landing />;
}
