# Music Theory MCP

Chat assistant that runs music theory tools (music21) with live notation. See `README.md` for the architecture and design decisions.

## Working agreement
- The user owns architecture and design decisions. Claude writes the syntax.
- Claude makes the design calls within a phase, lists them at the end, and the user reviews and overrules in batches.

## Architecture rules (enforced by import-linter)
- `core` never imports `server`.
- Only `core/engine` imports `music21`.
- `server/agent` never imports `core`; it reaches theory only through MCP.
- Every boundary is a typed Pydantic schema. Invalid input raises `TheoryError` (or a subclass).

## Layout
`core/{models,services,engine,tests}` · `server/{mcp_server.py,api,agent,store,tests}` · `web/` (React)

## Commands
- `uv sync`
- `uv run ruff check . && uv run ruff format --check .`
- `uv run lint-imports`
- `uv run pytest`
- `uv run --env-file .env uvicorn server.api.main:app --port 8000`
- `cd web && npm run dev` (or `npm run build`)

## Gotchas
- music21 is slow to import: it is imported inside functions, never at module level.
- Pitches use `Bb`, music21 uses `B-`. The conversion lives only in `core/engine/pitch.py`.
- The MCP SDK is 2.x: `MCPServer`, not `FastMCP`. Raise `ToolError` for failures the model should read.
- Chat history is append-only. Store Claude's replies unchanged, including thinking blocks.
- MCP tool descriptions are read by the model: keep tools small and output compact.
