// Friendly names for the generated API types (lib/api/schema.d.ts). Never hand-edit
// the schema: regenerate it with `make api-types` when the API changes.
import type { components } from "./schema";

type Schemas = components["schemas"];

export type CaseView = Schemas["CaseView"];
export type CaseEvent = Schemas["CaseEvent"];
export type TraceStep = Schemas["TraceStep"];
export type SourceView = Schemas["SourceView"];
export type MessageRecord = Schemas["MessageRecord"];
export type ReceiveAck = Schemas["ReceiveAck"];
export type OutboundMessage = Schemas["OutboundMessage"];
export type ReplayStatus = Schemas["ReplayStatus"];
export type Priority = Schemas["Priority"];
export type Channel = Schemas["Channel"];
export type Badge = Schemas["Badge"];
export type Location = Schemas["Location"];
export type MessageIn = Schemas["MessageIn"];
export type ReplayIn = Schemas["ReplayIn"];
