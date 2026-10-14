"""The typed events the agent streams to the browser, one per server-sent event."""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


class TextDelta(BaseModel):
    """A chunk of Claude's reply."""

    type: Literal["text_delta"] = "text_delta"
    text: str


class ToolCall(BaseModel):
    """Claude decided to call a tool, with these inputs."""

    type: Literal["tool_call"] = "tool_call"
    id: str
    name: str
    input: dict[str, Any]


class ToolResult(BaseModel):
    """A tool finished. `summary` is the compact result, or the error message on failure."""

    type: Literal["tool_result"] = "tool_result"
    id: str
    name: str
    status: Literal["ok", "error"]
    summary: Any


class ArtifactReady(BaseModel):
    """A score is ready for the notation panel to fetch by id."""

    type: Literal["artifact"] = "artifact"
    tool_call_id: str
    kind: str
    id: str


class Error(BaseModel):
    """Something went wrong. `recoverable` means the chat can carry on."""

    type: Literal["error"] = "error"
    message: str
    recoverable: bool


class Usage(BaseModel):
    """Tokens used across every request in the turn."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


class Done(BaseModel):
    """The turn is over."""

    type: Literal["done"] = "done"
    usage: Usage


Event = Annotated[
    TextDelta | ToolCall | ToolResult | ArtifactReady | Error | Done, Field(discriminator="type")
]


def to_sse(event: Event) -> str:
    """Format an event as one server-sent event."""
    return f"event: {event.type}\ndata: {event.model_dump_json()}\n\n"
