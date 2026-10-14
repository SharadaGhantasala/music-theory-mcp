import pytest

from core.engine.pitch import interval_between, transpose_pitch
from core.errors import InvalidNoteError


@pytest.mark.parametrize(
    ("pitch", "semitones", "expected"),
    [
        ("C4", 7, "G4"),
        ("Bb3", 2, "C4"),
        ("C4", 12, "C5"),
        ("C4", -1, "B3"),
        ("A4", 0, "A4"),
    ],
)
def test_transpose_pitch(pitch, semitones, expected):
    assert transpose_pitch(pitch, semitones) == expected


@pytest.mark.parametrize(
    ("low", "high", "expected"),
    [("C4", "G4", 7), ("Bb3", "C4", 2), ("C4", "C4", 0), ("G4", "C4", -7)],
)
def test_interval_between(low, high, expected):
    assert interval_between(low, high) == expected


@pytest.mark.parametrize("pitch", ["C4", "F#3", "Bb2", "E5"])
@pytest.mark.parametrize("semitones", [-14, -1, 3, 11, 19])
def test_transpose_up_then_down_keeps_pitch_height(pitch, semitones):
    moved = transpose_pitch(pitch, semitones)
    assert interval_between(pitch, moved) == semitones
    assert interval_between(moved, transpose_pitch(moved, -semitones)) == -semitones


@pytest.mark.parametrize("bad", ["banana", "C", "H4", "", "c4"])
def test_bad_pitch_raises_invalid_note(bad):
    with pytest.raises(InvalidNoteError):
        transpose_pitch(bad, 1)
    with pytest.raises(InvalidNoteError):
        interval_between("C4", bad)
