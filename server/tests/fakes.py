"""A stand-in for the Claude API that replays scripted replies, so tests need no API key."""

from types import SimpleNamespace
from typing import Any

from anthropic.types.beta import BetaMessage


def reply(*blocks: dict[str, Any], stop_reason: str | None = None) -> BetaMessage:
    """Build a Claude reply from content blocks."""
    has_tool_call = any(block["type"] == "tool_use" for block in blocks)
    return BetaMessage.model_validate(
        {
            "id": "msg_test",
            "type": "message",
            "role": "assistant",
            "model": "claude-test",
            "content": list(blocks),
            "stop_reason": stop_reason or ("tool_use" if has_tool_call else "end_turn"),
            "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }
    )


def text(value: str) -> dict[str, Any]:
    return {"type": "text", "text": value}


def tool_use(call_id: str, name: str, arguments: Any) -> dict[str, Any]:
    return {"type": "tool_use", "id": call_id, "name": name, "input": arguments}


class _Stream:
    def __init__(self, message: BetaMessage) -> None:
        self._message = message

    async def __aenter__(self) -> "_Stream":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def __aiter__(self):
        for block in self._message.content:
            if block.type == "text":
                # Split the text so tests see more than one delta.
                middle = len(block.text) // 2
                for piece in (block.text[:middle], block.text[middle:]):
                    if piece:
                        yield SimpleNamespace(type="text", text=piece)

    async def get_final_message(self) -> BetaMessage:
        return self._message


class FakeClaude:
    """Replays `script` one reply per request and records the requests it was sent.

    An exception in the script is raised instead of returned. When the script runs out,
    the last entry is repeated.
    """

    def __init__(self, *script: BetaMessage | Exception) -> None:
        self._script = list(script)
        self.requests: list[dict[str, Any]] = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(stream=self._stream))

    def _stream(self, **request: Any) -> _Stream:
        # Copy the messages: the loop keeps appending to the same list.
        self.requests.append({**request, "messages": list(request["messages"])})
        step = self._script[min(len(self.requests), len(self._script)) - 1]
        if isinstance(step, Exception):
            raise step
        return _Stream(step)
