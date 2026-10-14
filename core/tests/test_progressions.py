import pytest

from core.errors import AnalysisError, InvalidNoteError
from core.services.progressions import analyze_progression

C, F, G, AM = ["C4", "E4", "G4"], ["F4", "A4", "C5"], ["G4", "B4", "D5"], ["A3", "C4", "E4"]
G7 = ["G3", "B3", "D4", "F4"]
A_MINOR = [["A3", "C4", "E4"], ["D4", "F4", "A4"], ["E4", "G#4", "B4"], ["A3", "C4", "E4"]]


def _summary(progression):
    return (
        (progression.key.tonic, progression.key.mode),
        [c.roman for c in progression.chords],
        [(c.type, c.index) for c in progression.cadences],
    )


@pytest.mark.parametrize(
    ("chords", "expected"),
    [
        ([C, F, G, C], (("C", "major"), ["I", "IV", "V", "I"], [("authentic", 3)])),
        ([C, F, G7, C], (("C", "major"), ["I", "IV", "V7", "I"], [("authentic", 3)])),
        ([C, G, AM, F], (("C", "major"), ["I", "V", "vi", "IV"], [("deceptive", 2)])),
        ([C, F, C], (("C", "major"), ["I", "IV", "I"], [("plagal", 2)])),
        ([C, F, G], (("C", "major"), ["I", "IV", "V"], [("half", 2)])),
        (A_MINOR, (("A", "minor"), ["i", "iv", "V", "i"], [("authentic", 3)])),
    ],
)
def test_analyze_progression_detects_key(chords, expected):
    progression = analyze_progression(chords)
    assert _summary(progression) == expected
    assert progression.key_detected is True


def test_analyze_progression_in_a_given_key():
    progression = analyze_progression([C, F, G, C], tonic="G", mode="major")
    assert _summary(progression) == (("G", "major"), ["IV", "bVII", "I", "IV"], [])
    assert progression.key_detected is False


def test_ii_v_i_with_sevenths_in_b_flat():
    chords = [["C4", "Eb4", "G4", "Bb4"], ["F3", "A3", "C4", "Eb4"], ["Bb3", "D4", "F4", "A4"]]
    key, romans, cadences = _summary(analyze_progression(chords))
    assert key == ("Bb", "major")
    assert romans == ["ii7", "V7", "I7"]
    assert cadences == [("authentic", 2)]


def test_inversions_and_suspensions_get_figures():
    chords = [["E4", "G4", "C5"], ["G3", "C4", "D4"], G, C]
    romans = [c.roman for c in analyze_progression(chords, tonic="C").chords]
    assert romans == ["I6", "Vsus4", "V", "I"]


def test_minor_v_is_not_a_cadence():
    chords = [["A3", "C4", "E4"], ["E4", "G4", "B4"], ["A3", "C4", "E4"]]
    assert analyze_progression(chords, tonic="A", mode="minor").cadences == []


def test_chords_keep_their_identity():
    chord = analyze_progression([C, F, G, C]).chords[1].chord
    assert (chord.root, chord.quality, chord.pitches) == ("F", "major", F)


def test_bad_input():
    with pytest.raises(AnalysisError):
        analyze_progression([])
    with pytest.raises(AnalysisError, match="chord 2"):
        analyze_progression([C, ["C4", "D4", "E4"]])
    with pytest.raises(InvalidNoteError):
        analyze_progression([C, ["banana"]])
    with pytest.raises(InvalidNoteError):
        analyze_progression([C], tonic="H")
