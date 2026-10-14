from pydantic import BaseModel

from core.models.transposition import Direction


class Interval(BaseModel):
    """The distance between two pitches.

    `name` is the short form ("P5"), `description` the spoken one ("Perfect Fifth").
    `semitones` is signed: negative when the second pitch is lower than the first.
    """

    name: str
    description: str
    semitones: int
    direction: Direction
