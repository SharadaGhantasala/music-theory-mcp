from core.engine.pitch import split_note, to_name
from core.errors import InvalidNoteError, UnknownScaleError

# music21 class for each seven-note scale, most common first.
_CLASSES = {
    "major": "MajorScale",
    "natural_minor": "MinorScale",
    "harmonic_minor": "HarmonicMinorScale",
    "melodic_minor": "MelodicMinorScale",
    "dorian": "DorianScale",
    "mixolydian": "MixolydianScale",
    "lydian": "LydianScale",
    "phrygian": "PhrygianScale",
    "locrian": "LocrianScale",
}
# Pentatonics are a parent scale with two degrees left out (degrees are zero-based).
_SUBSETS = {
    "major_pentatonic": ("major", (0, 1, 2, 4, 5)),
    "minor_pentatonic": ("natural_minor", (0, 2, 3, 4, 6)),
}

SCALE_TYPES: tuple[str, ...] = (
    "major",
    "natural_minor",
    "major_pentatonic",
    "minor_pentatonic",
    "harmonic_minor",
    "melodic_minor",
    "dorian",
    "mixolydian",
    "lydian",
    "phrygian",
    "locrian",
)


def scale_notes(root: str, scale_type: str) -> list[str]:
    """Return the notes of a scale as pitch classes, starting on the root.

    scale_notes("Bb", "major") -> ["Bb", "C", "D", "Eb", "F", "G", "A"]
    scale_notes("A", "minor_pentatonic") -> ["A", "C", "D", "E", "G"]

    Raises InvalidNoteError on a bad root and UnknownScaleError on an unsupported type.
    """
    if scale_type in _SUBSETS:
        parent, degrees = _SUBSETS[scale_type]
        notes = scale_notes(root, parent)
        return [notes[degree] for degree in degrees]
    if scale_type not in _CLASSES:
        supported = ", ".join(SCALE_TYPES)
        raise UnknownScaleError(f"{scale_type!r} is not a supported scale; choose from {supported}")

    m21_root, octave = split_note(root)
    if octave is not None:
        raise InvalidNoteError(f"{root!r} is not a valid scale root; expected e.g. 'C' or 'Bb'")

    from music21 import scale as m21_scale

    pitches = getattr(m21_scale, _CLASSES[scale_type])(m21_root).pitches
    # music21 repeats the root an octave up at the end.
    return [to_name(p) for p in pitches[:-1]]
