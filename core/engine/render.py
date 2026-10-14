from core.engine.pitch import load_pitch


def _to_stream(events: list[list[str]]):
    """Build a music21 stream with one note or chord per event."""
    parsed = [[load_pitch(p) for p in pitches] for pitches in events]

    from music21 import chord as m21_chord
    from music21 import note as m21_note
    from music21 import stream as m21_stream

    score = m21_stream.Stream()
    for pitches in parsed:
        if len(pitches) == 1:
            score.append(m21_note.Note(pitches[0]))
        elif pitches:
            score.append(m21_chord.Chord(pitches))
    return score


def to_musicxml(events: list[list[str]]) -> str:
    """Render a sequence of notes and chords as a MusicXML document.

    Each event is a list of pitches sounding together: one pitch is a note, several are a chord.
    to_musicxml([["C4"], ["E4"], ["C4", "E4", "G4"]]) -> "<?xml ...>"

    Raises InvalidNoteError on a bad pitch.
    """
    score = _to_stream(events)

    from music21.musicxml.m21ToXml import GeneralObjectExporter

    return GeneralObjectExporter(score).parse().decode("utf-8")


def to_midi(events: list[list[str]]) -> bytes:
    """Render a sequence of notes and chords as a standard MIDI file.

    Raises InvalidNoteError on a bad pitch.
    """
    score = _to_stream(events)

    from music21.midi.translate import streamToMidiFile

    return streamToMidiFile(score).writestr()
