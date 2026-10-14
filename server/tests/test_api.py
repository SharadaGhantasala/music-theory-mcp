import json

import pytest
from fastapi.testclient import TestClient

from server.api.app import create_app
from server.config import Settings
from server.tests.fakes import FakeClaude, reply, text, tool_use

CHORDS = [["C4", "E4", "G4"], ["F4", "A4", "C5"], ["G4", "B4", "D5"], ["C4", "E4", "G4"]]


def _client(tmp_path, *script):
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        mcp_url="",
        web_dist=str(tmp_path / "missing"),
    )
    return TestClient(create_app(settings, claude=FakeClaude(*script)))


def _chat(client, message, session_id="s1"):
    response = client.post("/api/chat", json={"session_id": session_id, "message": message})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = []
    for chunk in response.text.strip().split("\n\n"):
        name, data = chunk.split("\n", 1)
        event = json.loads(data.removeprefix("data: "))
        assert name == f"event: {event['type']}"
        events.append(event)
    return events


def test_health(tmp_path):
    with _client(tmp_path, reply(text("hi"))) as client:
        assert client.get("/api/health").json() == {"status": "ok"}


def test_chat_streams_events_and_the_score_can_be_fetched(tmp_path):
    script = (
        reply(tool_use("call_1", "analyze_progression", {"chords": CHORDS})),
        reply(text("I, IV, V, I in C major.")),
    )
    with _client(tmp_path, *script) as client:
        events = _chat(client, "analyze C F G C")
        assert [e["type"] for e in events] == [
            "tool_call",
            "tool_result",
            "artifact",
            "text_delta",
            "text_delta",
            "done",
        ]
        artifact_id = events[2]["id"]

        score = client.get(f"/api/artifacts/{artifact_id}")
        assert score.status_code == 200
        assert "<score-partwise" in score.text

        assert client.get(f"/api/artifacts/{artifact_id}/events").json() == {"events": CHORDS}

        midi = client.get(f"/api/artifacts/{artifact_id}/midi")
        assert midi.headers["content-type"] == "audio/midi"
        assert midi.content.startswith(b"MThd")


def test_follow_up_sees_the_earlier_turn(tmp_path):
    claude_script = (reply(text("First answer.")), reply(text("Second answer.")))
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}", mcp_url="", web_dist="missing"
    )
    claude = FakeClaude(*claude_script)
    with TestClient(create_app(settings, claude=claude)) as client:
        _chat(client, "first question")
        _chat(client, "second question")
        _chat(client, "another chat", session_id="s2")

        assert [m["role"] for m in claude.requests[1]["messages"]] == ["user", "assistant", "user"]
        assert len(claude.requests[2]["messages"]) == 1

        saved = client.get("/api/sessions/s1/messages").json()
        assert saved == [
            {"role": "user", "text": "first question"},
            {"role": "assistant", "text": "First answer."},
            {"role": "user", "text": "second question"},
            {"role": "assistant", "text": "Second answer."},
        ]


def test_tool_traffic_is_hidden_from_saved_messages(tmp_path):
    script = (
        reply(text("Checking."), tool_use("call_1", "identify_chord", {"pitches": CHORDS[0]})),
        reply(text("C major.")),
    )
    with _client(tmp_path, *script) as client:
        _chat(client, "what chord?")
        assert client.get("/api/sessions/s1/messages").json() == [
            {"role": "user", "text": "what chord?"},
            {"role": "assistant", "text": "Checking.\n\nC major."},
        ]


def test_missing_score_is_a_404(tmp_path):
    with _client(tmp_path, reply(text("hi"))) as client:
        assert client.get("/api/artifacts/nope").status_code == 404
        assert client.get("/api/artifacts/nope/midi").status_code == 404


@pytest.mark.parametrize("body", [{"session_id": "s1"}, {"session_id": "", "message": "hi"}])
def test_bad_chat_request_is_rejected(tmp_path, body):
    with _client(tmp_path, reply(text("hi"))) as client:
        assert client.post("/api/chat", json=body).status_code == 422
