import json

import pytest
from mcp import Client

from server.mcp_server import build_server
from server.store.artifacts import ArtifactStore
from server.store.db import open_database

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def store(tmp_path):
    return ArtifactStore(open_database(f"sqlite:///{tmp_path / 'test.db'}"))


@pytest.fixture
async def client(store):
    async with Client(build_server(store)) as connected:
        yield connected


async def test_lists_tools_resources_and_prompt(client):
    tools = {tool.name for tool in (await client.list_tools()).tools}
    assert tools == {
        "identify_chord",
        "get_scale",
        "detect_scales",
        "get_interval",
        "transpose",
        "analyze_progression",
    }
    resources = {str(r.uri) for r in (await client.list_resources()).resources}
    assert resources == {"theory://scale-types", "theory://chord-qualities"}
    assert [p.name for p in (await client.list_prompts()).prompts] == ["explain_progression"]


async def test_tool_schema_lists_allowed_scale_types(client):
    tools = {tool.name: tool for tool in (await client.list_tools()).tools}
    assert "dorian" in json.dumps(tools["get_scale"].input_schema)


async def test_identify_chord_returns_summary_and_stores_notation(client, store):
    result = await client.call_tool("identify_chord", {"pitches": ["E4", "G4", "C5"]})
    assert not result.is_error
    body = result.structured_content
    assert body["summary"]["root"] == "C"
    assert body["summary"]["quality"] == "major"
    assert body["artifact"]["kind"] == "musicxml"

    stored = store.get(body["artifact"]["id"])
    assert stored.events == [["E4", "G4", "C5"]]
    assert "<score-partwise" in stored.content


async def test_notation_never_reaches_the_model(client):
    result = await client.call_tool("analyze_progression", {"chords": [["C4", "E4", "G4"]] * 4})
    assert "score-partwise" not in result.model_dump_json()


async def test_get_scale_and_detect_scales(client):
    scale = await client.call_tool("get_scale", {"root": "Bb", "scale_type": "major"})
    assert scale.structured_content["summary"]["notes"] == ["Bb", "C", "D", "Eb", "F", "G", "A"]

    found = await client.call_tool("detect_scales", {"notes": "C D E F G A B C".split()})
    best = found.structured_content["summary"][0]
    assert (best["scale"]["root"], best["scale"]["type"]) == ("C", "major")


async def test_get_interval(client):
    result = await client.call_tool("get_interval", {"first": "C4", "second": "G4"})
    assert result.structured_content["summary"]["name"] == "P5"


async def test_analyze_progression(client):
    chords = [["C4", "E4", "G4"], ["F4", "A4", "C5"], ["G4", "B4", "D5"], ["C4", "E4", "G4"]]
    result = await client.call_tool("analyze_progression", {"chords": chords})
    summary = result.structured_content["summary"]
    assert [c["roman"] for c in summary["chords"]] == ["I", "IV", "V", "I"]
    assert summary["cadences"] == [{"type": "authentic", "index": 3}]


async def test_follow_up_transposes_an_earlier_score(client, store):
    chords = [["C4", "E4", "G4"], ["F4", "A4", "C5"]]
    first = await client.call_tool("analyze_progression", {"chords": chords})
    score_id = first.structured_content["artifact"]["id"]

    second = await client.call_tool("transpose", {"interval": "P4", "score_id": score_id})
    body = second.structured_content
    assert body["summary"]["semitones"] == 5
    assert body["artifact"]["id"] != score_id
    assert store.get(body["artifact"]["id"]).events == [["F4", "A4", "C5"], ["Bb4", "D5", "F5"]]


async def test_transpose_pitches(client):
    result = await client.call_tool(
        "transpose", {"interval": "m3", "direction": "down", "pitches": ["C4", "E4", "G4"]}
    )
    assert result.structured_content["summary"]["pitches"] == ["A3", "C#4", "E4"]


@pytest.mark.parametrize(
    ("tool", "arguments", "message"),
    [
        ("identify_chord", {"pitches": ["banana"]}, "not a valid"),
        ("identify_chord", {"pitches": ["C4", "D4", "E4"]}, "could not identify"),
        ("get_scale", {"root": "C", "scale_type": "bebop"}, "scale_type"),
        ("transpose", {"interval": "fourth", "pitches": ["C4"]}, "not a valid interval"),
        ("transpose", {"interval": "P4"}, "exactly one"),
        ("transpose", {"interval": "P4", "score_id": "missing"}, "no score with id"),
    ],
)
async def test_errors_come_back_as_readable_tool_errors(client, tool, arguments, message):
    result = await client.call_tool(tool, arguments)
    assert result.is_error
    assert message in result.content[0].text


async def test_resources_and_prompt(client):
    scale_types = await client.read_resource("theory://scale-types")
    assert "dorian" in json.loads(scale_types.contents[0].text)

    prompt = await client.get_prompt("explain_progression", {"chords": "C F G C"})
    assert "C F G C" in prompt.messages[0].content.text
