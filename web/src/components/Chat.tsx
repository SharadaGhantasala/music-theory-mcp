import { type FormEvent, type KeyboardEvent, useEffect, useRef, useState } from "react";

import type { Turn } from "../types";
import { ToolCard } from "./ToolCard";

const SUGGESTIONS = [
  "What chord is C, E, G, B?",
  "Analyze the progression C, Am, F, G in C major",
  "Which scale fits the notes D, E, F, G, A, B, C?",
  "Show me the Bb major scale, then transpose it up a fourth",
];

type Props = {
  turns: Turn[];
  busy: boolean;
  onSend: (message: string) => void;
  onShowScore: (artifactId: string) => void;
};

export function Chat({ turns, busy, onSend, onShowScore }: Props) {
  const [draft, setDraft] = useState("");
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottom.current?.scrollIntoView({ block: "end" });
  }, [turns]);

  const submit = (event?: FormEvent) => {
    event?.preventDefault();
    if (!draft.trim() || busy) return;
    onSend(draft);
    setDraft("");
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  };

  return (
    <section className="chat">
      <div className="messages">
        {turns.length === 0 ? (
          <div className="empty">
            <h2>Ask about any chord, scale or progression.</h2>
            <p>The answers come from real theory tools, and the notation appears beside the chat.</p>
            <div className="suggestions">
              {SUGGESTIONS.map((suggestion) => (
                <button key={suggestion} className="suggestion" onClick={() => onSend(suggestion)}>
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          turns.map((turn, index) => {
            const writing = busy && index === turns.length - 1 && turn.role === "assistant";
            return (
              <article key={turn.id} className={`turn ${turn.role}`}>
                <div className="label">{turn.role === "user" ? "You" : "Assistant"}</div>
                {turn.parts.map((part, partIndex) => {
                  if (part.kind === "text") {
                    return (
                      <p key={partIndex} className="text">
                        {part.text}
                      </p>
                    );
                  }
                  if (part.kind === "tool") {
                    return <ToolCard key={part.id} tool={part} onShowScore={onShowScore} />;
                  }
                  return (
                    <p key={partIndex} className="problem" role="alert">
                      {part.message}
                    </p>
                  );
                })}
                {writing && <span className="pulse" aria-label="Working" />}
              </article>
            );
          })
        )}
        <div ref={bottom} />
      </div>

      <form className="composer" onSubmit={submit}>
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask a music theory question"
          rows={2}
          aria-label="Message"
        />
        <button type="submit" className="primary" disabled={busy || !draft.trim()}>
          {busy ? "Working" : "Send"}
        </button>
      </form>
    </section>
  );
}
