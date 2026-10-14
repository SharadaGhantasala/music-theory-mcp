import { useCallback, useEffect, useRef, useState } from "react";

import { fetchSavedMessages, streamChat } from "./api";
import { AnalysisPanel } from "./components/AnalysisPanel";
import { Chat } from "./components/Chat";
import { CircleOfFifths } from "./components/CircleOfFifths";
import { Notation } from "./components/Notation";
import { keyOf } from "./keys";
import type { AgentEvent, Analysis, Part, Turn } from "./types";

const SESSION_KEY = "music-theory-mcp-session";

function loadSessionId(): string {
  const saved = localStorage.getItem(SESSION_KEY);
  if (saved) return saved;
  const created = crypto.randomUUID();
  localStorage.setItem(SESSION_KEY, created);
  return created;
}

/** Apply one streamed event to the parts of the assistant turn being written. */
function applyEvent(parts: Part[], event: AgentEvent): Part[] {
  switch (event.type) {
    case "text_delta": {
      const last = parts[parts.length - 1];
      if (last?.kind === "text") {
        return [...parts.slice(0, -1), { kind: "text", text: last.text + event.text }];
      }
      return [...parts, { kind: "text", text: event.text }];
    }
    case "tool_call":
      return [
        ...parts,
        { kind: "tool", id: event.id, name: event.name, input: event.input, status: "running" },
      ];
    case "tool_result":
      return parts.map((part) =>
        part.kind === "tool" && part.id === event.id
          ? { ...part, status: event.status, summary: event.summary }
          : part,
      );
    case "artifact":
      return parts.map((part) =>
        part.kind === "tool" && part.id === event.tool_call_id
          ? { ...part, artifactId: event.id }
          : part,
      );
    case "error":
      return [...parts, { kind: "error", message: event.message }];
    case "done":
      return parts;
  }
}

export function App() {
  const [sessionId, setSessionId] = useState(loadSessionId);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  const [artifactId, setArtifactId] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const turnCounter = useRef(0);

  const nextTurnId = () => `turn-${(turnCounter.current += 1)}`;

  // Bring back the text of an earlier chat after a page reload.
  useEffect(() => {
    let cancelled = false;
    fetchSavedMessages(sessionId)
      .then((saved) => {
        if (cancelled || saved.length === 0) return;
        setTurns(
          saved.map((message, index) => ({
            id: `saved-${index}`,
            role: message.role,
            parts: [{ kind: "text", text: message.text }],
          })),
        );
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  const send = useCallback(
    async (message: string) => {
      const text = message.trim();
      if (!text || busy) return;

      const assistantId = nextTurnId();
      setTurns((current) => [
        ...current,
        { id: nextTurnId(), role: "user", parts: [{ kind: "text", text }] },
        { id: assistantId, role: "assistant", parts: [] },
      ]);
      setBusy(true);

      const onEvent = (event: AgentEvent) => {
        if (event.type === "artifact") setArtifactId(event.id);
        if (event.type === "tool_result" && event.status === "ok") {
          setAnalysis({ tool: event.name, summary: event.summary });
        }
        setTurns((current) =>
          current.map((turn) =>
            turn.id === assistantId ? { ...turn, parts: applyEvent(turn.parts, event) } : turn,
          ),
        );
      };

      try {
        await streamChat(sessionId, text, onEvent);
      } catch (error) {
        const detail = error instanceof Error ? error.message : String(error);
        onEvent({ type: "error", message: `Could not reach the server. ${detail}`, recoverable: true });
      } finally {
        setBusy(false);
      }
    },
    [busy, sessionId],
  );

  const startNewChat = () => {
    const created = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, created);
    setSessionId(created);
    setTurns([]);
    setArtifactId(null);
    setAnalysis(null);
  };

  return (
    <div className="app">
      <header className="topbar">
        <h1 className="brand">
          <svg className="mark" viewBox="0 0 14 14" aria-hidden="true">
            <path d="M1 3v8M5 6v7M9 1v8M13 4v8" />
          </svg>
          Music Theory MCP
        </h1>
        <span className="caption topbar-caption">Theory tools — Claude — music21</span>
        <button className="link" onClick={startNewChat} disabled={busy}>
          New chat
        </button>
      </header>
      <main className="workspace">
        <Chat turns={turns} busy={busy} onSend={send} onShowScore={setArtifactId} />
        <section className="side">
          <Notation
            artifactId={artifactId}
            onExplain={(position, pitches) =>
              send(`Explain note or chord ${position} in the score on screen (${pitches.join(" ")}): what it is and what it does here.`)
            }
          />
          <div className="side-row">
            <AnalysisPanel analysis={analysis} />
            <CircleOfFifths focus={keyOf(analysis)} />
          </div>
        </section>
      </main>
    </div>
  );
}
