// Fixed API responses, so screenshots don't depend on AWS, models, or the clock.
import type { CaseView, MessageRecord, Priority, ReplayStatus } from "../../lib/api/types";

const AT = "2026-11-10T01:30:00Z";
const source = (id: string, sender: string, text: string, summary: string) => ({
  message_id: id,
  sender,
  channel: "sms" as const,
  received_at: AT,
  text,
  english_summary: summary,
  priority: "P1" as const,
});

const critical: CaseView = {
  case_id: "case-0001",
  status: "open",
  priority: "P1",
  priority_overridden: false,
  reason: "Infant and senior on the roof",
  english_summary: "5 people, including an infant and a senior, on the roof in Malanday.",
  location: { barangay: "Malanday", lat: 14.663, lng: 121.1, source: "text" },
  people_count: 5,
  vulnerable: ["infant", "senior"],
  water_level: "roof",
  medical_emergency: false,
  badges: ["corroborated"],
  assigned_team: null,
  opened_at: AT,
  last_seen: AT,
  history: [],
  sources: [
    {
      ...source(
        "m1",
        "+639000000002",
        "nasa bubong na kami 5 tao may baby",
        "5 people on the roof.",
      ),
      // Shaped like a real run's trace (agents/trace.py).
      trace: [
        { step: "normalize", status: "ran", duration_ms: 2, detail: "Cleaned the text" },
        { step: "prefilter", status: "ran", duration_ms: 1, detail: "Needs a model" },
        {
          step: "extract",
          status: "ran",
          duration_ms: 1420,
          detail: "5 people; infant; water: roof",
          service: "Bedrock · apac.amazon.nova-lite-v1:0",
        },
        {
          step: "geolocate",
          status: "ran",
          duration_ms: 3,
          detail: "Malanday, named in the message",
        },
        {
          step: "dedupe",
          status: "ran",
          duration_ms: 310,
          detail: "Opened case-0001",
          service: "Titan embeddings",
        },
        {
          step: "triage",
          status: "ran",
          duration_ms: 1105,
          detail: "P1: Infant and senior on the roof (0.88, confident)",
          service: "Bedrock · apac.amazon.nova-lite-v1:0",
        },
      ],
    },
    source("m2", "+639000000103", "pamilya ko sa malanday nasa bubong", "Family on the roof."),
  ],
};

const review: CaseView = {
  ...critical,
  history: [
    {
      action: "overridden",
      dispatcher: "Ana",
      at: AT,
      detail: "P2: Trapped upstairs, not on the roof",
    },
  ],
  case_id: "case-0002",
  priority: "P2",
  reason: "Trapped upstairs, water level unclear",
  english_summary: "4 people trapped on the 2nd floor in Tumana.",
  location: { barangay: "Tumana", lat: 14.656, lng: 121.096, source: "text" },
  vulnerable: [],
  water_level: "unknown",
  badges: ["needs_review"],
  sources: [
    {
      ...source("m3", "+639000000104", "2nd floor kami sa tumana", "4 people on the 2nd floor."),
      priority: "P2",
    },
  ],
};

const pending: CaseView = {
  ...review,
  history: [],
  case_id: "case-0003",
  priority: "P3",
  reason: "Can still move",
  english_summary: "3 people asking to evacuate.",
  location: { barangay: null, lat: null, lng: null, source: "unknown" },
  badges: ["awaiting_location"],
  sources: [],
};

export const CASES = [critical, review, pending];

// Only the fields the feed reads; one row per state it can show.
const outcome = (priority: Priority | null, is_suspicious = false) =>
  ({ priority, is_suspicious }) as MessageRecord["outcome"];
const record = (
  id: string,
  text: string,
  fields: Partial<Omit<MessageRecord, "message_id" | "message">>,
): MessageRecord => ({
  message_id: id,
  message: { sender: `+6390000001${id}`, text, channel: "sms", received_at: AT },
  kind: "triaged",
  outcome: null,
  case_id: null,
  ...fields,
});

export const MESSAGES: MessageRecord[] = [
  record("01", "nasa bubong na kami 5 tao may baby", { outcome: outcome("P1") }),
  record("02", "2nd floor kami sa tumana tumataas pa tubig", { outcome: outcome("P2") }),
  record("03", "Malanday po, sa tapat ng barangay hall", { kind: "location_reply" }),
  record("04", "pwede po ba lumikas ang pamilya namin", { outcome: outcome("P3") }),
  record("05", "ipasa nyo ito sa lahat, may rescue daw", { outcome: outcome("P4", true) }),
  record("06", "tulong po sa amin", { error: "triage failed" }),
];
export const REPLAY: ReplayStatus = { running: false, split: "dev", sent: 0, total: 0 };
