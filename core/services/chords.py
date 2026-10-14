from core.engine import chord as engine
from core.errors import AnalysisError
from core.models.chord import Chord


def identify_chord(pitches: list[str]) -> Chord:
    """Name the chord formed by `pitches`, e.g. ["E4", "G4", "C5"] -> C major over E4.

    Raises InvalidNoteError on a bad pitch and AnalysisError if the chord has no name we support.
    """
    found = engine.identify(pitches)
    if found is None:
        raise AnalysisError(f"could not identify a chord from {pitches}")
    root, quality, bass = found
    return Chord(root=root, quality=quality, pitches=pitches, bass=bass)
