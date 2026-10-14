import type { components } from "./api-types";

// The streamed events are generated from the backend's OpenAPI schema (npm run types).
type Schemas = components["schemas"];
export type TextDelta = Schemas["TextDelta"];
export type ToolCall = Schemas["ToolCall"];
export type ToolResult = Schemas["ToolResult"];
export type ArtifactReady = Schemas["ArtifactReady"];
export type ErrorEvent = Schemas["Error"];
export type Usage = Schemas["Usage"];
export type Done = Schemas["Done"];
export type AgentEvent = TextDelta | ToolCall | ToolResult | ArtifactReady | ErrorEvent | Done;

// Tool summaries travel as untyped JSON in the events. These mirror the models in core/models.
export type Chord = { root: string; quality: string; pitches: string[]; bass: string | null };
export type Scale = { root: string; type: string; notes: string[] };
export type ScaleMatch = { scale: Scale; score: number; outside: string[] };
export type Interval = { name: string; description: string; semitones: number; direction: string };
export type Transposition = {
  pitches: string[];
  interval: string;
  direction: string;
  semitones: number;
};
export type Progression = {
  key: { tonic: string; mode: string };
  key_detected: boolean;
  chords: { chord: Chord; roman: string; degree: number }[];
  cadences: { type: string; index: number }[];
};

// What the chat shows. An assistant turn is a sequence of text and tool calls, in order.
export type ToolPart = {
  kind: "tool";
  id: string;
  name: string;
  input: Record<string, unknown>;
  status: "running" | "ok" | "error";
  summary?: unknown;
  artifactId?: string;
};
export type Part = { kind: "text"; text: string } | ToolPart | { kind: "error"; message: string };
export type Turn = { id: string; role: "user" | "assistant"; parts: Part[] };

// The latest successful tool result, shown in the analysis panel.
export type Analysis = { tool: string; summary: unknown };
