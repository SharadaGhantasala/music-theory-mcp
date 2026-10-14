from core.engine import harmony as harmony_engine
from core.engine import interval as interval_engine
from core.errors import AnalysisError
from core.models.progression import AnalyzedChord, Cadence, Key, Mode, Progression
from core.services.chords import identify_chord

_DOMINANT_QUALITIES = {"major", "dominant7"}
_SUSPENDED_QUALITIES = {"sus2", "sus4"}

# Cadences read from the scale degrees of two neighbouring chords.
_CADENCES = {(5, 1): "authentic", (4, 1): "plagal", (5, 6): "deceptive"}


def analyze_progression(
    chords: list[list[str]], tonic: str | None = None, mode: Mode = "major"
) -> Progression:
    """Label each chord with a Roman numeral and find the cadences.

    `chords` is a list of chords, each a list of pitches, e.g. [["C4", "E4", "G4"], ...].
    Give `tonic` and `mode` to analyze in a known key, or leave `tonic` out to detect the key.

    Raises InvalidNoteError on a bad pitch or tonic, and AnalysisError if there are no
    chords or one of them has no name we support.
    """
    if not chords:
        raise AnalysisError("need at least one chord to analyze a progression")

    identified = []
    for position, pitches in enumerate(chords, start=1):
        try:
            identified.append(identify_chord(pitches))
        except AnalysisError as error:
            raise AnalysisError(f"chord {position}: {error}") from error

    key_detected = tonic is None
    if tonic is None:
        tonic, mode = harmony_engine.detect_key(chords)

    # music21 has no figure for sus chords, so they borrow the numeral of the major triad
    # on their root and get the suspension added on.
    readable = [
        _major_triad(c.root) if c.quality in _SUSPENDED_QUALITIES else c.pitches for c in identified
    ]
    numerals = harmony_engine.roman_numerals(readable, tonic, mode)

    analyzed = []
    for chord, (figure, degree) in zip(identified, numerals, strict=True):
        if chord.quality in _SUSPENDED_QUALITIES:
            figure += chord.quality
        analyzed.append(AnalyzedChord(chord=chord, roman=figure, degree=degree))

    return Progression(
        key=Key(tonic=tonic, mode=mode),
        key_detected=key_detected,
        chords=analyzed,
        cadences=_find_cadences(analyzed),
    )


def _major_triad(root: str) -> list[str]:
    low = f"{root}4"
    return [
        low,
        *interval_engine.transpose_by([low], "M3"),
        *interval_engine.transpose_by([low], "P5"),
    ]


def _find_cadences(chords: list[AnalyzedChord]) -> list[Cadence]:
    """Find cadences between neighbouring chords, plus a half cadence if the end rests on V."""
    cadences = []
    for index in range(1, len(chords)):
        before, after = chords[index - 1], chords[index]
        cadence = _CADENCES.get((before.degree, after.degree))
        # A cadence needs a real dominant: a minor v chord does not count.
        if before.degree == 5 and before.chord.quality not in _DOMINANT_QUALITIES:
            cadence = None
        if cadence is not None:
            cadences.append(Cadence(type=cadence, index=index))

    last = chords[-1]
    if len(chords) > 1 and last.degree == 5 and last.chord.quality in _DOMINANT_QUALITIES:
        cadences.append(Cadence(type="half", index=len(chords) - 1))
    return cadences
