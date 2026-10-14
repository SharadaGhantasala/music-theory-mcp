from core.engine.pitch import load_pitch, split_note, to_name
from core.errors import InvalidNoteError


def _load_chords(chords: list[list[str]]):
    from music21 import chord as m21_chord

    return [m21_chord.Chord([load_pitch(p) for p in pitches]) for pitches in chords]


def detect_key(chords: list[list[str]]) -> tuple[str, str]:
    """Guess the key of a chord progression, e.g. C, F, G, C -> ("C", "major").

    Returns (tonic, mode) where mode is "major" or "minor".
    Raises InvalidNoteError on a bad pitch.
    """
    from music21 import stream as m21_stream

    found = m21_stream.Stream(_load_chords(chords)).analyze("key")
    return to_name(found.tonic), found.mode


def roman_numerals(chords: list[list[str]], tonic: str, mode: str) -> list[tuple[str, int]]:
    """Return (figure, scale degree) for each chord in the given key.

    roman_numerals([["G3", "B3", "D4", "F4"]], "C", "major") -> [("V7", 5)]

    Raises InvalidNoteError on a bad pitch or tonic.
    """
    from music21 import key as m21_key
    from music21 import roman as m21_roman

    m21_tonic, octave = split_note(tonic)
    if octave is not None:
        raise InvalidNoteError(f"{tonic!r} is not a valid key; expected e.g. 'C' or 'Bb'")
    in_key = m21_key.Key(m21_tonic, mode)

    numerals = [m21_roman.romanNumeralFromChord(c, in_key) for c in _load_chords(chords)]
    return [(n.figure, n.scaleDegree) for n in numerals]
