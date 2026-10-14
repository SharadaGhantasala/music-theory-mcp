"""MCP server: exposes the core theory services as tools. No theory logic lives here."""

import json
from collections.abc import Callable
from functools import wraps
from typing import get_args

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel

from core.errors import TheoryError
from core.models.artifact import Artifact
from core.models.chord import Chord, ChordQuality
from core.models.interval import Interval
from core.models.progression import Mode, Progression
from core.models.scale import Scale, ScaleMatch, ScaleType
from core.models.transposition import Direction, Transposition
from core.services import chords, intervals, notation, progressions, scales
from core.services import transpose as transposition
from server.config import load_settings
from server.store.artifacts import ArtifactStore
from server.store.db import open_database

_INSTRUCTIONS = (
    "Music theory tools. Pitches are written with an octave, like C4, F#3 or Bb2. "
    "Pitch classes (roots, tonics) have no octave, like C or Bb. "
    "Every tool returns a compact `summary` and an `artifact` id for the rendered notation."
)


class ToolResult[T](BaseModel):
    """What every tool returns: a compact summary for the model and a handle to the notation.

    The notation itself (MusicXML) is saved in the store and never sent to the model.
    """

    summary: T
    artifact: Artifact


def readable_errors[**P, R](tool: Callable[P, R]) -> Callable[P, R]:
    """Turn a TheoryError into a tool error the model can read and recover from.

    The SDK hides the text of unexpected exceptions, so expected ones are converted here.
    """

    @wraps(tool)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return tool(*args, **kwargs)
        except TheoryError as error:
            raise ToolError(f"{type(error).__name__}: {error}") from error

    return wrapper


def build_server(store: ArtifactStore) -> MCPServer:
    """Create the MCP server with its tools, resources and prompt."""
    server = MCPServer("music-theory", instructions=_INSTRUCTIONS)

    def save_score(events: list[list[str]]) -> Artifact:
        content = notation.render_musicxml(events)
        return Artifact(kind="musicxml", id=store.save("musicxml", content, events))

    @server.tool()
    @readable_errors
    def identify_chord(pitches: list[str]) -> ToolResult[Chord]:
        """Name a chord from its pitches: root, quality and bass note.

        Use for "what chord is C E G?". Pitches need octaves, e.g. ["C4", "E4", "G4"].
        Recognises triads, seventh chords, sus2 and sus4; other chords return an error.
        """
        return ToolResult(summary=chords.identify_chord(pitches), artifact=save_score([pitches]))

    @server.tool()
    @readable_errors
    def get_scale(root: str, scale_type: ScaleType) -> ToolResult[Scale]:
        """List the notes of a scale, e.g. root "Bb" and scale_type "major".

        `root` is a pitch class without an octave.
        """
        scale = scales.get_scale(root, scale_type)
        events = [[pitch] for pitch in notation.ascending(scale.notes)]
        return ToolResult(summary=scale, artifact=save_score(events))

    @server.tool()
    @readable_errors
    def detect_scales(notes: list[str], limit: int = 5) -> ToolResult[list[ScaleMatch]]:
        """Rank the scales that best fit some notes, best first.

        Use for "what scale or key is this?". Notes may have octaves or not. To detect from
        chords, pass all of their notes in order. Each match has a 0-1 score and lists the
        notes that fall outside the scale. Few notes give close scores: say so if they do.
        The artifact shows the best match.
        """
        matches = scales.detect_scales(notes, limit)
        events = [[pitch] for pitch in notation.ascending(matches[0].scale.notes)]
        return ToolResult(summary=matches, artifact=save_score(events))

    @server.tool()
    @readable_errors
    def get_interval(first: str, second: str) -> ToolResult[Interval]:
        """Name the interval between two pitches, e.g. "C4" and "G4" is a perfect fifth (P5).

        Both pitches need octaves. `semitones` is negative when the second pitch is lower.
        """
        found = intervals.get_interval(first, second)
        return ToolResult(summary=found, artifact=save_score([[first], [second]]))

    @server.tool()
    @readable_errors
    def transpose(
        interval: str,
        direction: Direction = "up",
        pitches: list[str] | None = None,
        score_id: str | None = None,
    ) -> ToolResult[Transposition]:
        """Move pitches or a whole earlier score up or down by an interval.

        `interval` is a quality letter and a size, never a word: P4 perfect fourth, M3 major
        third, m3 minor third, M2 major second, A4 augmented fourth, d5 diminished fifth.
        So "up a fourth" is interval "P4", direction "up".

        Give exactly one of `pitches` (with octaves, treated as one chord) or `score_id`
        (the artifact id from an earlier result, to transpose that score and keep its layout).
        """
        if (pitches is None) == (score_id is None):
            raise ToolError("give exactly one of `pitches` or `score_id`")

        if pitches is not None:
            events = [pitches]
        else:
            stored = store.get(score_id)
            if stored is None:
                raise ToolError(f"no score with id {score_id!r}")
            events = stored.events

        moved = [transposition.transpose(event, interval, direction) for event in events]
        summary = Transposition(
            pitches=[pitch for result in moved for pitch in result.pitches],
            interval=interval,
            direction=direction,
            semitones=moved[0].semitones,
        )
        return ToolResult(summary=summary, artifact=save_score([r.pitches for r in moved]))

    @server.tool()
    @readable_errors
    def analyze_progression(
        chords: list[list[str]], tonic: str | None = None, mode: Mode = "major"
    ) -> ToolResult[Progression]:
        """Label a chord progression with Roman numerals and find its cadences.

        `chords` is a list of chords, each a list of pitches with octaves, in order.
        Leave `tonic` out to detect the key, or give `tonic` (pitch class) and `mode` to
        analyze in a known key. Cadence `index` is the zero-based chord the cadence lands on.
        """
        analysis = progressions.analyze_progression(chords, tonic, mode)
        return ToolResult(summary=analysis, artifact=save_score(chords))

    @server.resource("theory://scale-types", mime_type="application/json")
    def scale_types() -> str:
        """The scale types the scale tools understand."""
        return json.dumps(get_args(ScaleType))

    @server.resource("theory://chord-qualities", mime_type="application/json")
    def chord_qualities() -> str:
        """The chord qualities identify_chord can name."""
        return json.dumps(get_args(ChordQuality))

    @server.prompt()
    def explain_progression(chords: str) -> str:
        """Ask for a beginner-friendly walkthrough of a chord progression."""
        return (
            f"Analyze this chord progression: {chords}\n\n"
            "Use analyze_progression to get the key, Roman numerals and cadences. "
            "Then explain in plain language what each chord does and why the progression "
            "sounds the way it does, for someone new to music theory."
        )

    return server


def main() -> None:
    """Run over stdio, for Claude Desktop and the MCP Inspector."""
    build_server(ArtifactStore(open_database(load_settings().database_url))).run("stdio")


if __name__ == "__main__":
    main()
