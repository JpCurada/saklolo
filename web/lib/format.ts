// Display helpers shared by the dashboard. All UI copy is English.
import type { Badge, Channel, Priority } from "./api/types";

export const PRIORITY_LABEL: Record<Priority, string> = {
  P1: "P1 Critical",
  P2: "P2 High",
  P3: "P3 Moderate",
  P4: "P4 Info",
};

export const CHANNEL_LABEL: Record<Channel, string> = {
  sms: "SMS",
  messenger: "Messenger",
  telegram: "Telegram",
  web: "Web",
};

export const BADGE_LABEL: Record<Badge, string> = {
  corroborated: "Corroborated",
  suspicious: "Suspicious",
  reported_safe: "Reported safe",
  awaiting_location: "Awaiting location",
  needs_review: "Needs review",
  overridden: "Overridden",
};

export const LOCATION_SOURCE_LABEL: Record<string, string> = {
  text: "named in the message",
  geocoder: "found by Amazon Location",
  reply: "from the resident's reply",
  reviewer: "a reviewers' landmark match, awaiting the resident",
  unknown: "unknown",
};

/** Last four digits only: enough to tell senders apart on screen. */
export function shortSender(sender: string): string {
  return `···${sender.slice(-4)}`;
}

export function clockTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-PH", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Manila",
  });
}
