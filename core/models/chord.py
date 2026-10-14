import re
from typing import Literal

from pydantic import BaseModel, field_validator

from core.errors import InvalidNoteError

ChordQuality = Literal[
    "major",
    "minor",
    "diminished",
    "augmented",
    "dominant7",
    "major7",
    "minor7",
    "half_diminished7",
    "diminished7",
    "sus2",
    "sus4",
]

_PITCH_CLASS = re.compile(r"[A-G](##?|bb?)?")
_PITCH = re.compile(r"[A-G](##?|bb?)?-?\d+")


def _check(value: str, pattern: re.Pattern[str], expected: str) -> str:
    if not pattern.fullmatch(value):
        raise InvalidNoteError(f"{value!r} is not a valid note; expected {expected}")
    return value


class Chord(BaseModel):
    """A single identified chord.

    `root` is a pitch class without octave ("C", "F#", "Bb").
    `pitches` and `bass` carry octaves ("C4", "F#3", "Bb2").
    """

    root: str
    quality: ChordQuality
    pitches: list[str]
    bass: str | None = None

    @field_validator("root")
    @classmethod
    def _valid_root(cls, value: str) -> str:
        return _check(value, _PITCH_CLASS, 'a pitch class like "C" or "Bb"')

    @field_validator("pitches")
    @classmethod
    def _valid_pitches(cls, values: list[str]) -> list[str]:
        return [_check(v, _PITCH, 'a pitch with octave like "C4" or "F#3"') for v in values]

    @field_validator("bass")
    @classmethod
    def _valid_bass(cls, value: str | None) -> str | None:
        return None if value is None else _check(value, _PITCH, 'a pitch with octave like "E3"')
