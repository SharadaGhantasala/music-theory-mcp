import type { AgentEvent } from "./types";

/** Send a message and call `onEvent` for each typed event the agent streams back. */
export async function streamChat(
  sessionId: string,
  message: string,
  onEvent: (event: AgentEvent) => void,
): Promise<void> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!response.ok || !response.body) {
    throw new Error(`The server answered ${response.status}.`);
  }

  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value;
    // Server-sent events are separated by a blank line.
    let end = buffer.indexOf("\n\n");
    while (end !== -1) {
      const data = buffer
        .slice(0, end)
        .split("\n")
        .find((line) => line.startsWith("data: "));
      if (data) onEvent(JSON.parse(data.slice("data: ".length)) as AgentEvent);
      buffer = buffer.slice(end + 2);
      end = buffer.indexOf("\n\n");
    }
  }
}

export async function fetchSavedMessages(
  sessionId: string,
): Promise<{ role: "user" | "assistant"; text: string }[]> {
  const response = await fetch(`/api/sessions/${sessionId}/messages`);
  return response.ok ? response.json() : [];
}

export async function fetchMusicXml(artifactId: string): Promise<string> {
  const response = await fetch(`/api/artifacts/${artifactId}`);
  if (!response.ok) throw new Error("Could not load the score.");
  return response.text();
}

export async function fetchScoreEvents(artifactId: string): Promise<string[][]> {
  const response = await fetch(`/api/artifacts/${artifactId}/events`);
  if (!response.ok) throw new Error("Could not load the notes.");
  return ((await response.json()) as { events: string[][] }).events;
}

export function midiUrl(artifactId: string): string {
  return `/api/artifacts/${artifactId}/midi`;
}
