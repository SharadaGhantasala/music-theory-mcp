from collections import Counter
from functools import cache

from core.engine import pitch as pitch_engine
from core.engine import scale as scale_engine
from core.errors import AnalysisError
from core.models.scale import Scale, ScaleMatch

# How much each kind of evidence counts towards a match score. They add up to 1.
_FIT_WEIGHT = 0.6  # share of the input notes that belong to the scale
_COVERAGE_WEIGHT = 0.15  # share of the scale's notes that appear in the input
_TONIC_WEIGHT = 0.15  # signs that the scale's root is the home note
_COMMONNESS_WEIGHT = 0.1  # head start for scales that turn up more often in real music

# How often each scale type turns up, from 0 (rare) to 1 (everywhere).
_COMMONNESS = {
    "major": 1.0,
    "natural_minor": 1.0,
    "major_pentatonic": 1.0,
    "minor_pentatonic": 1.0,
    "harmonic_minor": 0.5,
    "melodic_minor": 0.5,
    "dorian": 0.5,
    "mixolydian": 0.5,
    "lydian": 0.25,
    "phrygian": 0.25,
    "locrian": 0.0,
}

# Usual spelling of each of the 12 roots, for scales with a major or a minor third.
_MAJOR_ROOTS = ("C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
_MINOR_ROOTS = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B")
_MINOR_THIRD = 3


def get_scale(root: str, scale_type: str) -> Scale:
    """Return the scale of `scale_type` on `root`, e.g. ("Bb", "major") -> Bb C D Eb F G A.

    Raises InvalidNoteError on a bad root and UnknownScaleError on an unsupported type.
    """
    return Scale(root=root, type=scale_type, notes=scale_engine.scale_notes(root, scale_type))


@cache
def _shape(scale_type: str) -> frozenset[int]:
    """Return a scale type's notes as semitones above its root."""
    return frozenset(pitch_engine.pitch_class(n) for n in scale_engine.scale_notes("C", scale_type))


def detect_scales(notes: list[str], limit: int = 5) -> list[ScaleMatch]:
    """Rank the scales that best fit `notes`, best first, returning at most `limit`.

    Notes may carry octaves or not ("C4" or "C"), and repeats count as extra weight.
    To detect from chords, pass all of their notes in order.

    Raises InvalidNoteError on a bad note and AnalysisError if `notes` is empty.
    """
    if not notes:
        raise AnalysisError("need at least one note to detect a scale")

    classes = [pitch_engine.pitch_class(note) for note in notes]
    counts = Counter(classes)

    ranked = []
    for order, scale_type in enumerate(scale_engine.SCALE_TYPES):
        shape = _shape(scale_type)
        for root in range(12):
            members = {(root + step) % 12 for step in shape}
            fit = sum(n for pc, n in counts.items() if pc in members) / len(classes)
            coverage = len(members & counts.keys()) / len(members)
            # Starting on the root is the strongest sign, then ending on it, then just using it.
            starts, ends = classes[0] == root, classes[-1] == root
            tonic = 0.5 * starts + 0.25 * ends + 0.25 * (root in counts)
            score = (
                _FIT_WEIGHT * fit
                + _COVERAGE_WEIGHT * coverage
                + _TONIC_WEIGHT * tonic
                + _COMMONNESS_WEIGHT * _COMMONNESS[scale_type]
            )
            # Ties go to the scale type listed first, then to the lower root.
            ranked.append((-score, order, root, scale_type, members))
    ranked.sort()

    matches = []
    for negative_score, _, root, scale_type, members in ranked[:limit]:
        roots = _MINOR_ROOTS if _MINOR_THIRD in _shape(scale_type) else _MAJOR_ROOTS
        outside = [n for n, pc in zip(notes, classes, strict=True) if pc not in members]
        matches.append(
            ScaleMatch(
                scale=get_scale(roots[root], scale_type),
                score=round(-negative_score, 2),
                outside=list(dict.fromkeys(outside)),
            )
        )
    return matches
