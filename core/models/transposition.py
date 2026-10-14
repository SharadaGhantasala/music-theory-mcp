from typing import Literal

from pydantic import BaseModel

Direction = Literal["up", "down"]


class Transposition(BaseModel):
    """The result of transposing some pitches.

    `interval` is the name that was applied, such as "P4".
    `semitones` is the signed distance moved, negative when transposing down.
    """

    pitches: list[str]
    interval: str
    direction: Direction
    semitones: int
