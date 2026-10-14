"""The agent loop: Claude decides, MCP tools run, typed events stream out.

The agent never imports the theory core. It only speaks MCP to reach the tools.
"""

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import anthropic
import anyio
from anthropic import AsyncAnthropic
from mcp import Client

from server.agent.events import ArtifactReady, Done, Error, Event, TextDelta, ToolCall, ToolResult
from server.agent.events import Usage as TurnUsage
from server.agent.prompt import SYSTEM_PROMPT
from server.config import Settings

_FALLBACK_BETA = "server-side-fallback-2026-07-01"
_MAX_JSON_RETRIES = 2


@dataclass(frozen=True)
class _Outcome:
    """What one tool call produced: text for Claude and, on success, the parsed result."""

    ok: bool
    text: str
    summary: Any = None
    artifact: dict[str, str] | None = None


async def list_tools(mcp: Client) -> list[dict[str, Any]]:
    """Fetch the MCP server's tools in the shape the Claude API expects."""
    listed = await mcp.list_tools()
    return [
        {
            "name": tool.name,
            "description": tool.description or "",
            "input_schema": tool.input_schema,
            # Stream tool inputs as they are generated. The MCP server validates every
            # input against its schema, so a malformed one comes back as a tool error.
            "eager_input_streaming": True,
        }
        # A stable order keeps the prompt cache valid between requests.
        for tool in sorted(listed.tools, key=lambda tool: tool.name)
    ]


async def _call_tool(mcp: Client, name: str, arguments: Any, timeout: float) -> _Outcome:
    """Run one tool through MCP. Failures become text Claude can read, never exceptions."""
    if not isinstance(arguments, dict):
        return _Outcome(ok=False, text=json.dumps({"INVALID_JSON": json.dumps(arguments)}))
    try:
        with anyio.fail_after(timeout):
            result = await mcp.call_tool(name, arguments)
    except TimeoutError:
        return _Outcome(ok=False, text=f"The {name} tool timed out after {timeout:g} seconds.")
    except Exception as error:  # noqa: BLE001 - any MCP failure is reported back to Claude
        return _Outcome(ok=False, text=f"The {name} tool could not be reached: {error}")

    text = "\n".join(block.text for block in result.content if block.type == "text")
    body = result.structured_content
    if result.is_error or not isinstance(body, dict):
        return _Outcome(ok=False, text=text or f"The {name} tool failed.")
    return _Outcome(
        ok=True,
        text=json.dumps(body, separators=(",", ":")),
        summary=body.get("summary"),
        artifact=body.get("artifact"),
    )


async def _call_tools(mcp: Client, calls: list[Any], timeout: float) -> list[_Outcome]:
    """Run several tool calls at once and return their outcomes in the same order."""
    outcomes: list[_Outcome | None] = [None] * len(calls)

    async def run(index: int, call: Any) -> None:
        outcomes[index] = await _call_tool(mcp, call.name, call.input, timeout)

    async with anyio.create_task_group() as group:
        for index, call in enumerate(calls):
            group.start_soon(run, index, call)
    return [outcome for outcome in outcomes if outcome is not None]


def _request(settings: Settings, tools: list[dict[str, Any]], messages: list[dict]) -> dict:
    request: dict[str, Any] = {
        "model": settings.model,
        "max_tokens": settings.max_tokens,
        "system": SYSTEM_PROMPT,
        "tools": tools,
        "messages": messages,
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": settings.effort},
        # Cache the growing conversation so each round only pays for what is new.
        "cache_control": {"type": "ephemeral"},
    }
    if settings.refusal_fallback:
        request["betas"] = [_FALLBACK_BETA]
        request["fallbacks"] = "default"
    return request


def _api_error_message(error: anthropic.APIError) -> str:
    if isinstance(error, anthropic.AuthenticationError):
        return "The Anthropic API key was rejected. Check ANTHROPIC_API_KEY."
    if isinstance(error, anthropic.RateLimitError):
        return "The Claude API is rate limiting this app. Wait a moment and try again."
    if isinstance(error, anthropic.APIConnectionError):
        return "Could not reach the Claude API. Check your internet connection."
    if isinstance(error, anthropic.APIStatusError):
        return f"The Claude API returned an error ({error.status_code}): {error.message}"
    return f"The Claude API request failed: {error}"


async def run_turn(
    claude: AsyncAnthropic, mcp: Client, messages: list[dict[str, Any]], settings: Settings
) -> AsyncIterator[Event]:
    """Answer the last user message in `messages`, yielding events as things happen.

    New assistant and tool-result messages are appended to `messages`, so the caller can
    save them. The last event is always `Done`.
    """
    usage = TurnUsage()
    try:
        tools = await list_tools(mcp)
    except Exception as error:  # noqa: BLE001 - reported to the browser as an event
        yield Error(message=f"Could not load the theory tools: {error}", recoverable=False)
        yield Done(usage=usage)
        return

    json_retries = 0
    rounds = 0
    while True:
        try:
            async with claude.beta.messages.stream(**_request(settings, tools, messages)) as stream:
                async for event in stream:
                    if event.type == "text":
                        yield TextDelta(text=event.text)
                reply = await stream.get_final_message()
        except ValueError:
            # A tool input the SDK could not parse at all. Ask again, a bounded number of times.
            json_retries += 1
            if json_retries > _MAX_JSON_RETRIES:
                yield Error(message="Claude kept sending unreadable tool input.", recoverable=True)
                break
            continue
        except anthropic.APIError as error:
            yield Error(message=_api_error_message(error), recoverable=False)
            break
        json_retries = 0

        usage.input_tokens += reply.usage.input_tokens
        usage.output_tokens += reply.usage.output_tokens
        usage.cache_read_input_tokens += reply.usage.cache_read_input_tokens or 0
        usage.cache_creation_input_tokens += reply.usage.cache_creation_input_tokens or 0

        # Keep the reply exactly as sent: thinking blocks must be passed back unchanged.
        messages.append({"role": "assistant", "content": reply.to_dict()["content"]})

        calls = [block for block in reply.content if block.type == "tool_use"]
        if reply.stop_reason == "refusal":
            yield Error(message="Claude declined to answer that request.", recoverable=True)
            break
        if reply.stop_reason == "pause_turn":
            continue
        if not calls:
            break
        if reply.stop_reason == "max_tokens":
            # The tool input was cut off, so it must not be run. Close the calls with errors
            # to keep the history valid.
            cut_off = [
                _tool_result(call.id, _Outcome(ok=False, text="Input was cut off."))
                for call in calls
            ]
            messages.append({"role": "user", "content": cut_off})
            yield Error(message="Claude ran out of room mid tool call.", recoverable=True)
            break

        for call in calls:
            yield ToolCall(id=call.id, name=call.name, input=_as_dict(call.input))

        outcomes = await _call_tools(mcp, calls, settings.tool_timeout_seconds)

        results = []
        for call, outcome in zip(calls, outcomes, strict=True):
            results.append(_tool_result(call.id, outcome))
            yield ToolResult(
                id=call.id,
                name=call.name,
                status="ok" if outcome.ok else "error",
                summary=outcome.summary if outcome.ok else outcome.text,
            )
            if outcome.artifact:
                yield ArtifactReady(
                    tool_call_id=call.id, kind=outcome.artifact["kind"], id=outcome.artifact["id"]
                )
        # All results go back in one message, so Claude keeps calling tools in parallel.
        messages.append({"role": "user", "content": results})

        rounds += 1
        if rounds >= settings.max_tool_rounds:
            yield Error(
                message=f"Stopped after {rounds} rounds of tool calls without a final answer.",
                recoverable=True,
            )
            break

    yield Done(usage=usage)


def _tool_result(tool_use_id: str, outcome: _Outcome) -> dict[str, Any]:
    result: dict[str, Any] = {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": outcome.text,
    }
    if not outcome.ok:
        result["is_error"] = True
    return result


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {"value": value}
