from typing import Literal

from pydantic import BaseModel

from core.models.chord import Chord

Mode = Literal["major", "minor"]
CadenceType = Literal["authentic", "plagal", "half", "deceptive"]


class Key(BaseModel):
    """A key: its tonic as a pitch class and its mode."""

    tonic: str
    mode: Mode


class AnalyzedChord(BaseModel):
    """A chord in a progression with its Roman numeral and scale degree in the key."""

    chord: Chord
    roman: str
    degree: int


class Cadence(BaseModel):
    """A cadence, where `index` is the zero-based position of the chord it lands on."""

    type: CadenceType
    index: int


class Progression(BaseModel):
    """A chord progression analyzed in a key.

    `key_detected` is True when the key was guessed from the chords rather than given.
    """

    key: Key
    key_detected: bool
    chords: list[AnalyzedChord]
    cadences: list[Cadence]
