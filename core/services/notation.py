from core.engine import render as engine

_LETTERS = "CDEFGAB"


def render_musicxml(events: list[list[str]]) -> str:
    """Render notes and chords as MusicXML, e.g. [["C4"], ["C4", "E4", "G4"]].

    Each event is a list of pitches sounding together. Raises InvalidNoteError on a bad pitch.
    """
    return engine.to_musicxml(events)


def ascending(notes: list[str], octave: int = 4) -> list[str]:
    """Give octaves to pitch classes so they climb, e.g. ["A", "B", "C"] -> ["A4", "B4", "C5"]."""
    pitches = []
    previous = -1
    for note in notes:
        letter = _LETTERS.index(note[0])
        if letter < previous:
            octave += 1
        previous = letter
        pitches.append(f"{note}{octave}")
    return pitches
