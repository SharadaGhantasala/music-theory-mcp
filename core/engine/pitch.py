import re

from core.errors import InvalidNoteError

_NOTE = re.compile(r"([A-G])(##?|bb?)?(-?\d+)?")


def split_note(name: str) -> tuple[str, int | None]:
    """Split a note string into its music21 name and its octave, if it has one."""
    match = _NOTE.fullmatch(name)
    if match is None:
        raise InvalidNoteError(f"{name!r} is not a valid note; expected e.g. 'C', 'Bb' or 'F#3'")
    letter, accidental, octave = match.groups()
    # music21 spells flats with "-", so "Bb" becomes "B-".
    m21_name = letter + (accidental or "").replace("b", "-")
    return m21_name, None if octave is None else int(octave)


def load_pitch(name: str):
    """Parse a pitch string like "Bb3" into a music21 Pitch.

    Imports music21 lazily so importing `core` stays fast.
    """
    from music21 import pitch as m21_pitch

    m21_name, octave = split_note(name)
    if octave is None:
        raise InvalidNoteError(f"{name!r} is not a valid pitch; expected e.g. 'C4' or 'Bb3'")
    return m21_pitch.Pitch(name=m21_name, octave=octave)


def to_name(pitch) -> str:
    """Format a music21 Pitch as a pitch class in our spelling, e.g. "Bb"."""
    return pitch.name.replace("-", "b")


def to_str(pitch) -> str:
    """Format a music21 Pitch back into our "Bb3" spelling."""
    return to_name(pitch) + str(pitch.octave)


def pitch_class(note: str) -> int:
    """pitch_class("C") -> 0, pitch_class("Bb3") -> 10. The octave is optional and ignored.

    Raises InvalidNoteError on a bad note.
    """
    from music21 import pitch as m21_pitch

    m21_name, _ = split_note(note)
    return m21_pitch.Pitch(m21_name).pitchClass


def transpose_pitch(pitch: str, semitones: int) -> str:
    """transpose_pitch("C4", 7) -> "G4" and transpose_pitch("Bb3", 2) -> "C4".

    Negative `semitones` transposes down. Raises InvalidNoteError on a bad pitch.
    """
    return to_str(load_pitch(pitch).transpose(semitones))


def interval_between(low: str, high: str) -> int:
    """interval_between("C4", "G4") -> 7 and interval_between("Bb3", "C4") -> 2.

    Returns signed semitones from `low` to `high`, negative if `high` is lower.
    Raises InvalidNoteError on a bad pitch.
    """
    return round(load_pitch(high).ps - load_pitch(low).ps)
