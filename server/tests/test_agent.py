import json

import anthropic
import anyio
import httpx2
import pytest
from mcp import Client
from mcp.server.mcpserver import MCPServer

from server.agent.loop import list_tools, run_turn
from server.config import Settings
from server.mcp_server import build_server
from server.store.artifacts import ArtifactStore
from server.store.db import open_database
from server.tests.fakes import FakeClaude, reply, text, tool_use

pytestmark = pytest.mark.anyio

SETTINGS = Settings(max_tool_rounds=3, tool_timeout_seconds=0.2)
C_MAJOR = {"pitches": ["C4", "E4", "G4"]}


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def store(tmp_path):
    return ArtifactStore(open_database(f"sqlite:///{tmp_path / 'test.db'}"))


@pytest.fixture
async def mcp(store):
    async with Client(build_server(store)) as connected:
        yield connected


async def _run(claude, mcp, messages=None, settings=SETTINGS):
    messages = messages if messages is not None else [{"role": "user", "content": "hi"}]
    events = [event async for event in run_turn(claude, mcp, messages, settings)]
    return events, messages


def _types(events):
    return [event.type for event in events]


async def test_tools_come_from_mcp_in_a_stable_order(mcp):
    tools = await list_tools(mcp)
    names = [tool["name"] for tool in tools]
    assert names == sorted(names)
    assert "identify_chord" in names
    assert all(tool["input_schema"]["type"] == "object" for tool in tools)


async def test_plain_answer_streams_text_then_done(mcp):
    events, messages = await _run(FakeClaude(reply(text("A cadence ends a phrase."))), mcp)
    assert _types(events) == ["text_delta", "text_delta", "done"]
    assert "".join(e.text for e in events[:2]) == "A cadence ends a phrase."
    assert events[-1].usage.input_tokens == 10
    assert [m["role"] for m in messages] == ["user", "assistant"]


async def test_tool_call_runs_through_mcp_and_emits_typed_events(mcp, store):
    claude = FakeClaude(
        reply(text("Let me check."), tool_use("call_1", "identify_chord", C_MAJOR)),
        reply(text("That is C major.")),
    )
    events, messages = await _run(claude, mcp)

    assert _types(events) == [
        "text_delta",
        "text_delta",
        "tool_call",
        "tool_result",
        "artifact",
        "text_delta",
        "text_delta",
        "done",
    ]
    call, result, artifact = events[2], events[3], events[4]
    assert (call.name, call.input) == ("identify_chord", C_MAJOR)
    assert (result.status, result.summary["quality"]) == ("ok", "major")
    assert store.get(artifact.id).events == [C_MAJOR["pitches"]]
    assert events[-1].usage.output_tokens == 10

    assert [m["role"] for m in messages] == ["user", "assistant", "user", "assistant"]
    sent_back = messages[2]["content"][0]
    assert sent_back["tool_use_id"] == "call_1"
    assert json.loads(sent_back["content"])["artifact"]["id"] == artifact.id


async def test_notation_never_enters_the_conversation(mcp):
    claude = FakeClaude(reply(tool_use("call_1", "identify_chord", C_MAJOR)), reply(text("Done.")))
    events, messages = await _run(claude, mcp)
    assert "score-partwise" not in json.dumps(messages)
    assert "score-partwise" not in "".join(e.model_dump_json() for e in events)


async def test_tool_error_goes_back_to_claude_so_it_can_recover(mcp):
    claude = FakeClaude(
        reply(tool_use("call_1", "identify_chord", {"pitches": ["banana"]})),
        reply(tool_use("call_2", "identify_chord", C_MAJOR)),
        reply(text("C major.")),
    )
    events, messages = await _run(claude, mcp)

    results = [e for e in events if e.type == "tool_result"]
    assert [r.status for r in results] == ["error", "ok"]
    assert "InvalidNoteError" in results[0].summary
    failed = messages[2]["content"][0]
    assert failed["is_error"] is True
    assert "banana" in failed["content"]
    assert events[-2].type == "text_delta"


async def test_parallel_tool_calls_return_in_one_message(mcp):
    claude = FakeClaude(
        reply(
            tool_use("call_1", "identify_chord", C_MAJOR),
            tool_use("call_2", "get_interval", {"first": "C4", "second": "G4"}),
        ),
        reply(text("Both done.")),
    )
    events, messages = await _run(claude, mcp)
    assert [e.id for e in events if e.type == "tool_result"] == ["call_1", "call_2"]
    assert [r["tool_use_id"] for r in messages[2]["content"]] == ["call_1", "call_2"]


async def test_loop_stops_at_the_round_cap(mcp):
    claude = FakeClaude(reply(tool_use("call_1", "identify_chord", C_MAJOR)))
    events, messages = await _run(claude, mcp)

    assert len(claude.requests) == SETTINGS.max_tool_rounds
    assert _types(events)[-2:] == ["error", "done"]
    assert events[-2].recoverable is True
    # The history still ends on tool results, so the next turn is valid.
    assert messages[-1]["content"][0]["type"] == "tool_result"


async def test_slow_tool_times_out_and_the_turn_carries_on():
    slow_server = MCPServer("slow")

    @slow_server.tool()
    async def slow() -> str:
        """Takes too long."""
        await anyio.sleep(5)
        return "late"

    claude = FakeClaude(reply(tool_use("call_1", "slow", {})), reply(text("It timed out.")))
    async with Client(slow_server) as mcp:
        events, _ = await _run(claude, mcp)

    result = next(e for e in events if e.type == "tool_result")
    assert result.status == "error"
    assert "timed out" in result.summary
    assert _types(events)[-2:] == ["text_delta", "done"]


async def test_cut_off_tool_input_is_not_run(mcp, store):
    claude = FakeClaude(
        reply(tool_use("call_1", "identify_chord", C_MAJOR), stop_reason="max_tokens")
    )
    events, messages = await _run(claude, mcp)
    assert _types(events) == ["error", "done"]
    assert messages[-1]["content"][0]["is_error"] is True


async def test_refusal_is_reported(mcp):
    events, _ = await _run(FakeClaude(reply(stop_reason="refusal")), mcp)
    assert _types(events) == ["error", "done"]
    assert events[0].recoverable is True


async def test_api_failure_becomes_an_error_event(mcp):
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    failure = anthropic.APIConnectionError(request=request)
    events, messages = await _run(FakeClaude(failure), mcp)
    assert _types(events) == ["error", "done"]
    assert events[0].recoverable is False
    assert "reach the Claude API" in events[0].message
    assert len(messages) == 1


async def test_request_uses_settings_and_stays_append_only(mcp):
    claude = FakeClaude(reply(tool_use("call_1", "identify_chord", C_MAJOR)), reply(text("Done.")))
    await _run(claude, mcp)

    first, second = claude.requests
    assert first["model"] == SETTINGS.model
    assert first["output_config"] == {"effort": SETTINGS.effort}
    assert first["fallbacks"] == "default"
    assert "tool_choice" not in first
    assert second["messages"][: len(first["messages"])] == first["messages"]
