# Music Theory MCP

Chat assistant that runs music theory tools (music21) with live notation. Build plan: `~/Downloads/music-theory-mcp-build-plan.pdf`.

## Working agreement
- The user owns architecture and design decisions. Claude writes the syntax once a decision is made.
- Per phase: state the decisions, user decides, Claude implements, user explains it back, then commit.

## Architecture rules (enforced by import-linter)
- `core` never imports `server`.
- Only `core/engine` imports `music21`.
- `server/agent` never imports `core`; it reaches theory only through MCP.
- Every boundary is a typed Pydantic schema. Invalid input raises `TheoryError` (or a subclass).

## Layout
`core/{models,services,engine,tests}` · `server/{mcp_server.py,api,agent,store}` · `web/` (later)

## Commands
- `uv sync`
- `uv run ruff check . && uv run ruff format --check .`
- `uv run lint-imports`
- `uv run pytest`

## Gotchas
- music21 is slow to import: lazy-load and cache.
- Uploaded files are untrusted: limit size, accept only MusicXML, MIDI, ABC.
- MCP tool descriptions are read by the model: keep tools small and output compact.
