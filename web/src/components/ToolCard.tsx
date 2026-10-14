import { useState } from "react";

import { TOOL_LABELS } from "../format";
import type { ToolPart } from "../types";

type Props = { tool: ToolPart; onShowScore: (artifactId: string) => void };

/** A collapsible card for one tool call: what was asked, and what came back. */
export function ToolCard({ tool, onShowScore }: Props) {
  const [open, setOpen] = useState(false);
  const label = TOOL_LABELS[tool.name] ?? tool.name;

  return (
    <div className={`tool ${tool.status}`}>
      <button className="tool-head" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span className="pill">Tool</span>
        <span className="tool-name">{label}</span>
        <span className="tool-status">
          {tool.status === "running" && "Running"}
          {tool.status === "ok" && <span className="check">✓</span>}
          {tool.status === "error" && "Failed"}
        </span>
      </button>
      {open && (
        <div className="tool-body">
          <div className="label">Input</div>
          <pre>{JSON.stringify(tool.input, null, 2)}</pre>
          {tool.summary !== undefined && (
            <>
              <div className="label">{tool.status === "error" ? "Error" : "Result"}</div>
              <pre>
                {typeof tool.summary === "string"
                  ? tool.summary
                  : JSON.stringify(tool.summary, null, 2)}
              </pre>
            </>
          )}
          {tool.artifactId && (
            <button className="ghost" onClick={() => onShowScore(tool.artifactId!)}>
              Show this score
            </button>
          )}
        </div>
      )}
    </div>
  );
}
