import xml.etree.ElementTree as ET

import pytest

from core.errors import InvalidNoteError
from core.services.notation import ascending, render_midi, render_musicxml


def test_render_musicxml_is_well_formed():
    root = ET.fromstring(render_musicxml([["C4"], ["Bb3", "D4", "F4"]]).encode())
    assert root.tag == "score-partwise"
    assert [step.text for step in root.iter("step")] == ["C", "B", "D", "F"]


def test_render_musicxml_structure():
    document = render_musicxml([["C4"], ["Bb3", "D4", "F4"]])
    assert document.startswith("<?xml")
    assert "<score-partwise" in document
    assert document.count("<note") == 4
    assert document.count("<chord") == 2
    assert "<alter>-1</alter>" in document


def test_render_midi_is_a_midi_file():
    assert render_midi([["C4"], ["C4", "E4", "G4"]]).startswith(b"MThd")


def test_render_rejects_bad_pitch():
    with pytest.raises(InvalidNoteError):
        render_musicxml([["C"]])
    with pytest.raises(InvalidNoteError):
        render_midi([["C"]])


@pytest.mark.parametrize(
    ("notes", "expected"),
    [
        ("C D E F G A B", "C4 D4 E4 F4 G4 A4 B4"),
        ("A B C D E F G", "A4 B4 C5 D5 E5 F5 G5"),
        ("F# G# A# B C# D# E#", "F#4 G#4 A#4 B4 C#5 D#5 E#5"),
        ("A C D E G", "A4 C5 D5 E5 G5"),
    ],
)
def test_ascending(notes, expected):
    assert ascending(notes.split()) == expected.split()
