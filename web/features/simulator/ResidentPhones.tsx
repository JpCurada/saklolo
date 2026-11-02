"use client";

import Image from "next/image";
import Link from "next/link";

import { Badge, Text } from "@/components/ui";

import { PhoneSimulator } from "./PhoneSimulator";

/** Three simulated resident phones, one per channel, for demos and the video. */
export function ResidentPhones() {
  return (
    <div className="sk-shell">
      <header data-testid="resident-header" className="sk-header">
        <div className="sk-brand">
          <Image src="/assets/logo-mark.svg" width={32} height={32} alt="" unoptimized />
          <Text as="h1" variant="title-m">
            Resident phones
          </Text>
        </div>
        <span data-testid="simulated-label">
          <Badge tone="none">Demo phones · messages go through the real Saklolo pipeline</Badge>
        </span>
        <Link href="/dispatch" className="ml-auto" data-testid="open-dispatch">
          <Text variant="body-bold">Open dispatch</Text>
        </Link>
      </header>
      <main className="sk-phones">
        <PhoneSimulator channel="sms" testId="phone-sms" defaultSender="+639000000901" />
        <PhoneSimulator
          channel="telegram"
          testId="phone-telegram"
          defaultSender="telegram:demo-1"
        />
        <PhoneSimulator
          channel="messenger"
          testId="phone-messenger"
          defaultSender="messenger:demo-1"
        />
      </main>
    </div>
  );
}
