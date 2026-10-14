from core.engine.pitch import load_pitch


def to_musicxml(events: list[list[str]]) -> str:
    """Render a sequence of notes and chords as a MusicXML document.

    Each event is a list of pitches sounding together: one pitch is a note, several are a chord.
    to_musicxml([["C4"], ["E4"], ["C4", "E4", "G4"]]) -> "<?xml ...>"

    Raises InvalidNoteError on a bad pitch.
    """
    parsed = [[load_pitch(p) for p in pitches] for pitches in events]

    from music21 import chord as m21_chord
    from music21 import note as m21_note
    from music21 import stream as m21_stream
    from music21.musicxml.m21ToXml import GeneralObjectExporter

    score = m21_stream.Stream()
    for pitches in parsed:
        if len(pitches) == 1:
            score.append(m21_note.Note(pitches[0]))
        elif pitches:
            score.append(m21_chord.Chord(pitches))
    return GeneralObjectExporter(score).parse().decode("utf-8")
