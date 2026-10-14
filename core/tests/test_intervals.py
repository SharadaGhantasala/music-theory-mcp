import pytest

from core.errors import InvalidNoteError
from core.services.intervals import get_interval


@pytest.mark.parametrize(
    ("first", "second", "name", "description", "semitones", "direction"),
    [
        ("C4", "G4", "P5", "Perfect Fifth", 7, "up"),
        ("C4", "E4", "M3", "Major Third", 4, "up"),
        ("C4", "Eb4", "m3", "Minor Third", 3, "up"),
        ("C4", "F#4", "A4", "Augmented Fourth", 6, "up"),
        ("C4", "Gb4", "d5", "Diminished Fifth", 6, "up"),
        ("G4", "C4", "P5", "Perfect Fifth", -7, "down"),
        ("C4", "C5", "P8", "Perfect Octave", 12, "up"),
        ("C4", "C4", "P1", "Perfect Unison", 0, "up"),
        ("C4", "D5", "M9", "Major Ninth", 14, "up"),
    ],
)
def test_get_interval(first, second, name, description, semitones, direction):
    found = get_interval(first, second)
    assert (found.name, found.description, found.semitones, found.direction) == (
        name,
        description,
        semitones,
        direction,
    )


def test_bad_pitch_raises_invalid_note():
    with pytest.raises(InvalidNoteError):
        get_interval("C4", "G")
