from core.engine import interval as engine
from core.models.interval import Interval


def get_interval(first: str, second: str) -> Interval:
    """Name the interval from `first` to `second`, e.g. ("C4", "G4") -> P5, Perfect Fifth, 7.

    Raises InvalidNoteError on a bad pitch.
    """
    name, description, semitones = engine.describe(first, second)
    return Interval(
        name=name,
        description=description,
        semitones=semitones,
        direction="down" if semitones < 0 else "up",
    )
