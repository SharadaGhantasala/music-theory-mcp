import pytest

from core.errors import AnalysisError, InvalidNoteError
from core.services.chords import identify_chord


@pytest.mark.parametrize(
    ("pitches", "root", "quality", "bass"),
    [
        (["C4", "E4", "G4"], "C", "major", "C4"),
        (["E4", "G4", "C5"], "C", "major", "E4"),
        (["A3", "C4", "E4"], "A", "minor", "A3"),
        (["Bb3", "D4", "F4"], "Bb", "major", "Bb3"),
        (["B3", "D4", "F4"], "B", "diminished", "B3"),
        (["C4", "E4", "G#4"], "C", "augmented", "C4"),
        (["G3", "B3", "D4", "F4"], "G", "dominant7", "G3"),
        (["C4", "E4", "G4", "B4"], "C", "major7", "C4"),
        (["C4", "Eb4", "G4", "Bb4"], "C", "minor7", "C4"),
        (["B3", "D4", "F4", "A4"], "B", "half_diminished7", "B3"),
        (["B3", "D4", "F4", "Ab4"], "B", "diminished7", "B3"),
        (["C4", "D4", "G4"], "C", "sus2", "C4"),
        (["C4", "F4", "G4"], "C", "sus4", "C4"),
        (["C3", "G3", "E4", "C5"], "C", "major", "C3"),
    ],
)
def test_identify_chord(pitches, root, quality, bass):
    chord = identify_chord(pitches)
    assert (chord.root, chord.quality, chord.bass) == (root, quality, bass)
    assert chord.pitches == pitches


@pytest.mark.parametrize("pitches", [[], ["C4"], ["C4", "C5"], ["C4", "D4", "E4"]])
def test_unnamed_chord_raises_analysis_error(pitches):
    with pytest.raises(AnalysisError):
        identify_chord(pitches)


def test_bad_pitch_raises_invalid_note():
    with pytest.raises(InvalidNoteError):
        identify_chord(["C4", "banana", "G4"])
