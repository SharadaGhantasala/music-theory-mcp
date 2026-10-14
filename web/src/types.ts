// These mirror the Pydantic models in server/agent/events.py and core/models.

export type TextDelta = { type: "text_delta"; text: string };
export type ToolCall = { type: "tool_call"; id: string; name: string; input: Record<string, unknown> };
export type ToolResult = {
  type: "tool_result";
  id: string;
  name: string;
  status: "ok" | "error";
  summary: unknown;
};
export type ArtifactReady = { type: "artifact"; tool_call_id: string; kind: string; id: string };
export type ErrorEvent = { type: "error"; message: string; recoverable: boolean };
export type Usage = {
  input_tokens: number;
  output_tokens: number;
  cache_read_input_tokens: number;
  cache_creation_input_tokens: number;
};
export type Done = { type: "done"; usage: Usage };

export type AgentEvent = TextDelta | ToolCall | ToolResult | ArtifactReady | ErrorEvent | Done;

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
