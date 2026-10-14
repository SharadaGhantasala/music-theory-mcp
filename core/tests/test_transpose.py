import pytest
from pydantic import ValidationError

from core.engine.pitch import interval_between
from core.errors import InvalidIntervalError, InvalidNoteError
from core.services.transpose import transpose


@pytest.mark.parametrize(
    ("pitches", "interval", "direction", "expected", "semitones"),
    [
        ("C4 E4 G4", "P4", "up", "F4 A4 C5", 5),
        ("C4 E4 G4", "P4", "down", "G3 B3 D4", -5),
        ("C#4", "P4", "up", "F#4", 5),
        ("Bb3 D4 F4", "M2", "up", "C4 E4 G4", 2),
        ("C4 E4 G4", "m3", "down", "A3 C#4 E4", -3),
        ("C4", "P8", "up", "C5", 12),
        ("C4", "P1", "up", "C4", 0),
        # Same distance, different spelling: the interval name picks the letter.
        ("C4", "A4", "up", "F#4", 6),
        ("C4", "d5", "up", "Gb4", 6),
    ],
)
def test_transpose(pitches, interval, direction, expected, semitones):
    result = transpose(pitches.split(), interval, direction)
    assert result.pitches == expected.split()
    assert (result.interval, result.direction, result.semitones) == (interval, direction, semitones)


def test_transpose_defaults_to_up():
    assert transpose(["C4"], "M3").pitches == ["E4"]


@pytest.mark.parametrize("interval", ["m2", "M3", "P4", "A4", "d5", "P5", "M7", "M9"])
@pytest.mark.parametrize("pitches", [["C4", "E4", "G4"], ["F#3", "Bb4"], ["Eb2"]])
def test_up_then_down_returns_the_original(pitches, interval):
    up = transpose(pitches, interval, "up")
    assert transpose(up.pitches, interval, "down").pitches == pitches
    assert all(
        interval_between(a, b) == up.semitones for a, b in zip(pitches, up.pitches, strict=True)
    )


@pytest.mark.parametrize("interval", ["P3", "M4", "P0", "fourth", "4", "", "p4"])
def test_bad_interval_raises_invalid_interval(interval):
    with pytest.raises(InvalidIntervalError):
        transpose(["C4"], interval)


def test_bad_pitch_raises_invalid_note():
    with pytest.raises(InvalidNoteError):
        transpose(["C"], "P4")


def test_bad_direction_is_rejected():
    with pytest.raises(ValidationError):
        transpose(["C4"], "P4", "sideways")
