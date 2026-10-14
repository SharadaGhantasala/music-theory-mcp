from core.engine import interval as engine
from core.models.transposition import Direction, Transposition


def transpose(pitches: list[str], interval: str, direction: Direction = "up") -> Transposition:
    """Move `pitches` by a named interval, e.g. (["C4", "E4", "G4"], "P4") -> F4 A4 C5.

    `interval` is a quality letter and a size: "P4" perfect fourth, "m3" minor third,
    "M2" major second, "A4" augmented fourth, "d5" diminished fifth.

    Raises InvalidNoteError on a bad pitch and InvalidIntervalError on a bad interval.
    """
    down = direction == "down"
    moved = engine.transpose_by(pitches, interval, down=down)
    distance = engine.semitones(interval)
    return Transposition(
        pitches=moved,
        interval=interval,
        direction=direction,
        semitones=-distance if down else distance,
    )
