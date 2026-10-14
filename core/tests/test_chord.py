import pytest

from core.errors import InvalidNoteError, TheoryError
from core.models.chord import Chord


def test_valid_chord():
    chord = Chord(root="Bb", quality="major", pitches=["Bb3", "D4", "F4"], bass="D4")
    assert chord.bass == "D4"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"root": "banana", "pitches": ["C4"]},
        {"root": "H", "pitches": ["C4"]},
        {"root": "C4", "pitches": ["C4"]},
        {"root": "C", "pitches": ["C"]},
        {"root": "C", "pitches": ["C4"], "bass": "E"},
    ],
)
def test_invalid_notes_are_rejected(kwargs):
    with pytest.raises(InvalidNoteError):
        Chord(quality="major", **kwargs)


def test_invalid_note_is_a_theory_error():
    with pytest.raises(TheoryError):
        Chord(root="banana", quality="major", pitches=["C4"])
