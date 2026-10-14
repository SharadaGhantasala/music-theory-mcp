from core.engine.pitch import load_pitch, to_str

# Pitch classes above the root, in semitones, for each chord quality we name.
_TERTIAN = {
    frozenset({0, 4, 7}): "major",
    frozenset({0, 3, 7}): "minor",
    frozenset({0, 3, 6}): "diminished",
    frozenset({0, 4, 8}): "augmented",
    frozenset({0, 4, 7, 10}): "dominant7",
    frozenset({0, 4, 7, 11}): "major7",
    frozenset({0, 3, 7, 10}): "minor7",
    frozenset({0, 3, 6, 10}): "half_diminished7",
    frozenset({0, 3, 6, 9}): "diminished7",
}
_SUSPENDED = {
    frozenset({0, 2, 7}): "sus2",
    frozenset({0, 5, 7}): "sus4",
}


def _shape(pitches, root) -> frozenset[int]:
    """Return the set of semitone distances of `pitches` above `root`, ignoring octaves."""
    return frozenset((p.pitchClass - root.pitchClass) % 12 for p in pitches)


def identify(pitches: list[str]) -> tuple[str, str, str] | None:
    """Return (root, quality, bass) for the chord, or None if we have no name for it.

    identify(["E4", "G4", "C5"]) -> ("C", "major", "E4")
    identify(["C4", "F4", "G4"]) -> ("C", "sus4", "C4")

    `root` is a pitch class, `bass` is the lowest pitch with its octave.
    Raises InvalidNoteError on a bad pitch.
    """
    parsed = [load_pitch(p) for p in pitches]
    if not parsed:
        return None

    from music21 import chord as m21_chord

    m21 = m21_chord.Chord(parsed)
    root, bass = m21.root(), m21.bass()

    # music21 finds roots by stacking thirds, which is unreliable for sus chords,
    # so those are read from the bass first.
    candidates = [(root, _TERTIAN), (bass, _SUSPENDED), (root, _SUSPENDED)]
    for candidate, table in candidates:
        quality = table.get(_shape(parsed, candidate))
        if quality is not None:
            return candidate.name.replace("-", "b"), quality, to_str(bass)
    return None
