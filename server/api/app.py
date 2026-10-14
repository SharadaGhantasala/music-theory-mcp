"""The web backend: chat streaming, score downloads and the MCP endpoint, in one process."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from anthropic import AnthropicError, AsyncAnthropic
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from mcp import Client
from pydantic import BaseModel, Field

from core.services import notation
from server.agent.events import Done, Error, Usage, to_sse
from server.agent.loop import run_turn
from server.config import Settings, load_settings
from server.mcp_server import build_server
from server.store.artifacts import ArtifactStore, StoredArtifact
from server.store.chats import ChatStore
from server.store.db import open_database

_MUSICXML = "application/vnd.recordare.musicxml+xml"
_NO_CREDENTIALS = (
    "No Anthropic API key found. Put ANTHROPIC_API_KEY in a .env file and restart the server."
)


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=4000)


class ChatMessage(BaseModel):
    """One visible turn of a saved chat."""

    role: str
    text: str


class ScoreEvents(BaseModel):
    """The notes and chords of a score, in order, for playback."""

    events: list[list[str]]


def create_app(settings: Settings | None = None, claude: AsyncAnthropic | None = None) -> FastAPI:
    """Build the app. `claude` can be passed in so tests can use a stand-in."""
    settings = settings or load_settings()
    engine = open_database(settings.database_url)
    artifacts = ArtifactStore(engine)
    chats = ChatStore(engine)
    mcp_server = build_server(artifacts)
    mcp_app = mcp_server.streamable_http_app(streamable_http_path="/mcp")

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        async with mcp_server.session_manager.run():
            yield

    app = FastAPI(title="Music Theory MCP", lifespan=lifespan)

    def connect_to_mcp() -> Client:
        # Over HTTP by default, so the agent uses the same door as any other MCP client.
        return Client(settings.mcp_url) if settings.mcp_url else Client(mcp_server)

    def stored(artifact_id: str) -> StoredArtifact:
        artifact = artifacts.get(artifact_id)
        if artifact is None:
            raise HTTPException(status_code=404, detail="No score with that id.")
        return artifact

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/chat")
    async def chat(request: ChatRequest) -> StreamingResponse:
        """Answer a message, streaming typed events (see server/agent/events.py)."""

        async def events() -> AsyncIterator[str]:
            messages = chats.load(request.session_id)
            saved = len(messages)
            messages.append({"role": "user", "content": request.message})
            try:
                client = claude or AsyncAnthropic()
                if not _has_credentials(client):
                    raise AnthropicError(_NO_CREDENTIALS)
                async with connect_to_mcp() as mcp:
                    async for event in run_turn(client, mcp, messages, settings):
                        yield to_sse(event)
            except AnthropicError as error:
                yield to_sse(Error(message=str(error), recoverable=False))
                yield to_sse(Done(usage=Usage()))
            except Exception as error:  # noqa: BLE001 - the browser must always get an ending
                # Errors raised inside the MCP connection arrive wrapped in a group.
                while isinstance(error, BaseExceptionGroup) and error.exceptions:
                    error = error.exceptions[0]
                yield to_sse(Error(message=f"The chat failed: {error}", recoverable=False))
                yield to_sse(Done(usage=Usage()))
            finally:
                chats.append(request.session_id, messages[saved:])

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/sessions/{session_id}/messages")
    def session_messages(session_id: str) -> list[ChatMessage]:
        """Return the visible text of a saved chat, without tool traffic."""
        visible = []
        for message in chats.load(session_id):
            text = _visible_text(message["content"])
            if text:
                visible.append(ChatMessage(role=message["role"], text=text))
        return visible

    @app.get("/api/artifacts/{artifact_id}")
    def artifact_musicxml(artifact_id: str) -> Response:
        return Response(stored(artifact_id).content, media_type=_MUSICXML)

    @app.get("/api/artifacts/{artifact_id}/events")
    def artifact_events(artifact_id: str) -> ScoreEvents:
        return ScoreEvents(events=stored(artifact_id).events)

    @app.get("/api/artifacts/{artifact_id}/midi")
    def artifact_midi(artifact_id: str) -> Response:
        midi = notation.render_midi(stored(artifact_id).events)
        headers = {"Content-Disposition": f'attachment; filename="{artifact_id}.mid"'}
        return Response(midi, media_type="audio/midi", headers=headers)

    # The MCP endpoint lives beside the REST routes, at /mcp.
    app.router.routes.extend(mcp_app.routes)

    if Path(settings.web_dist).is_dir():
        app.mount("/", StaticFiles(directory=settings.web_dist, html=True), name="web")

    return app


def _has_credentials(client: Any) -> bool:
    return bool(getattr(client, "api_key", True) or getattr(client, "auth_token", None))


def _visible_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if block.get("type") == "text")
