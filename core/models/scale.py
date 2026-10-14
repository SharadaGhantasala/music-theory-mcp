from typing import Literal

from pydantic import BaseModel

ScaleType = Literal[
    "major",
    "natural_minor",
    "major_pentatonic",
    "minor_pentatonic",
    "harmonic_minor",
    "melodic_minor",
    "dorian",
    "mixolydian",
    "lydian",
    "phrygian",
    "locrian",
]


class Scale(BaseModel):
    """A scale: its root, its type, and its notes as pitch classes starting on the root."""

    root: str
    type: ScaleType
    notes: list[str]


class ScaleMatch(BaseModel):
    """One candidate scale for a set of notes.

    `score` runs from 0 to 1, higher is a better match.
    `outside` lists the input notes that are not in the scale.
    """

    scale: Scale
    score: float
    outside: list[str]
