from typing import get_args

import pytest

from core.engine.scale import SCALE_TYPES
from core.errors import AnalysisError, InvalidNoteError, UnknownScaleError
from core.models.scale import ScaleType
from core.services.scales import detect_scales, get_scale


def test_model_and_engine_agree_on_scale_types():
    assert get_args(ScaleType) == SCALE_TYPES


@pytest.mark.parametrize(
    ("root", "scale_type", "notes"),
    [
        ("C", "major", "C D E F G A B"),
        ("Bb", "major", "Bb C D Eb F G A"),
        ("F#", "major", "F# G# A# B C# D# E#"),
        ("A", "natural_minor", "A B C D E F G"),
        ("A", "harmonic_minor", "A B C D E F G#"),
        ("A", "melodic_minor", "A B C D E F# G#"),
        ("D", "dorian", "D E F G A B C"),
        ("G", "mixolydian", "G A B C D E F"),
        ("F", "lydian", "F G A B C D E"),
        ("E", "phrygian", "E F G A B C D"),
        ("B", "locrian", "B C D E F G A"),
        ("C", "major_pentatonic", "C D E G A"),
        ("A", "minor_pentatonic", "A C D E G"),
    ],
)
def test_get_scale(root, scale_type, notes):
    scale = get_scale(root, scale_type)
    assert scale.notes == notes.split()
    assert (scale.root, scale.type) == (root, scale_type)


def test_get_scale_rejects_bad_input():
    with pytest.raises(UnknownScaleError):
        get_scale("C", "bebop")
    with pytest.raises(InvalidNoteError):
        get_scale("banana", "major")
    with pytest.raises(InvalidNoteError):
        get_scale("C4", "major")


def _best(notes: str) -> tuple[str, str]:
    top = detect_scales(notes.split())[0]
    return top.scale.root, top.scale.type


@pytest.mark.parametrize(
    ("notes", "expected"),
    [
        ("C D E F G A B C", ("C", "major")),
        ("A B C D E F G A", ("A", "natural_minor")),
        ("A B C D E F G# A", ("A", "harmonic_minor")),
        ("D E F G A B C D", ("D", "dorian")),
        ("G A B C D E F G", ("G", "mixolydian")),
        ("C D E G A C", ("C", "major_pentatonic")),
        ("A C D E G A", ("A", "minor_pentatonic")),
        ("Bb3 C4 D4 Eb4 F4 G4 A4 Bb4", ("Bb", "major")),
        # C, F and G major triads flattened into notes.
        ("C4 E4 G4 F4 A4 C5 G4 B4 D5 C4 E4 G4", ("C", "major")),
    ],
)
def test_detect_scales_best_match(notes, expected):
    assert _best(notes) == expected


@pytest.mark.parametrize(
    ("notes", "expected"),
    [
        # A scale run that stops short of the top note still reads as major, then its relative.
        ("C D E F G A B", [("C", "major"), ("A", "natural_minor")]),
        # An E minor seventh chord: E minor readings come before D major.
        ("E G B D", [("E", "minor_pentatonic"), ("E", "natural_minor"), ("D", "major")]),
        ("C E G A", [("C", "major_pentatonic"), ("C", "major")]),
    ],
)
def test_detect_scales_order(notes, expected):
    matches = detect_scales(notes.split(), limit=len(expected))
    assert [(m.scale.root, m.scale.type) for m in matches] == expected


def test_every_scale_type_wins_on_its_own_run():
    for scale_type in SCALE_TYPES:
        notes = get_scale("D", scale_type).notes
        top = detect_scales([*notes, "D"])[0]
        assert (top.scale.root, top.scale.type) == ("D", scale_type)


def test_detect_scales_ranks_and_scores():
    matches = detect_scales("C D E F G A B C".split(), limit=4)
    scores = [m.score for m in matches]
    assert len(matches) == 4
    assert scores == sorted(scores, reverse=True)
    assert all(0 <= score <= 1 for score in scores)
    assert matches[0].outside == []


def test_detect_scales_reports_notes_outside_the_scale():
    matches = detect_scales("C D E F G A B F#4 C".split(), limit=20)
    c_major = next(m for m in matches if (m.scale.root, m.scale.type) == ("C", "major"))
    assert c_major.outside == ["F#4"]


def test_detect_scales_ignores_octaves():
    assert _best("C4 D5 E2 F4 G3 A4 B4 C6") == _best("C D E F G A B C")


def test_detect_scales_rejects_bad_input():
    with pytest.raises(AnalysisError):
        detect_scales([])
    with pytest.raises(InvalidNoteError):
        detect_scales(["C", "banana"])
