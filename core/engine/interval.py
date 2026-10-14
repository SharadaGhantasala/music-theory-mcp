import re

from core.engine.pitch import load_pitch, to_str
from core.errors import InvalidIntervalError

# A quality letter and a size: P perfect, M major, m minor, A augmented, d diminished.
_INTERVAL = re.compile(r"[PMmAd]\d+")


def _load_interval(name: str):
    """Parse an interval name like "P4" into a music21 Interval."""
    from music21 import interval as m21_interval

    if not _INTERVAL.fullmatch(name):
        raise InvalidIntervalError(
            f"{name!r} is not a valid interval; expected e.g. 'P4', 'm3' or 'M2'"
        )
    try:
        return m21_interval.Interval(name)
    except m21_interval.IntervalException as error:
        raise InvalidIntervalError(f"{name!r} is not a valid interval: {error}") from error


def semitones(interval: str) -> int:
    """semitones("P4") -> 5 and semitones("m3") -> 3.

    Raises InvalidIntervalError on a bad interval.
    """
    return _load_interval(interval).semitones


def transpose_by(pitches: list[str], interval: str, down: bool = False) -> list[str]:
    """Move every pitch by a named interval, keeping the spelling the interval implies.

    transpose_by(["C#4"], "P4") -> ["F#4"]
    transpose_by(["C4", "E4", "G4"], "m3", down=True) -> ["A3", "C#4", "E4"]

    Raises InvalidNoteError on a bad pitch and InvalidIntervalError on a bad interval.
    """
    step = _load_interval(interval)
    if down:
        step = step.reverse()
    return [to_str(load_pitch(p).transpose(step)) for p in pitches]


def describe(low: str, high: str) -> tuple[str, str, int]:
    """Return (name, description, semitones) for the interval from `low` to `high`.

    describe("C4", "G4") -> ("P5", "Perfect Fifth", 7)
    describe("G4", "C4") -> ("P5", "Perfect Fifth", -7)

    `semitones` is negative when `high` is the lower pitch.
    Raises InvalidNoteError on a bad pitch.
    """
    from music21 import interval as m21_interval

    start, end = load_pitch(low), load_pitch(high)
    found = m21_interval.Interval(start, end)
    semitones = found.semitones
    if semitones < 0:
        # Name a falling interval by its rising form, so C#4 down to C4 is an augmented
        # unison, the same as C4 up to C#4. music21 would call it a diminished unison.
        found = m21_interval.Interval(end, start)
    return found.name, found.niceName, semitones
