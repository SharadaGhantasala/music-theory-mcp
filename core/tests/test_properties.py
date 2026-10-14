"""Property-based tests: facts that must hold for any valid input, not just chosen cases."""

from hypothesis import given, settings
from hypothesis import strategies as st

from core.engine.pitch import interval_between
from core.engine.scale import SCALE_TYPES
from core.services.chords import identify_chord
from core.services.intervals import get_interval
from core.services.scales import detect_scales, get_scale
from core.services.transpose import transpose

letters = st.sampled_from("CDEFGAB")
accidentals = st.sampled_from(["", "#", "b"])
pitch_classes = st.builds(lambda letter, accidental: letter + accidental, letters, accidentals)
octaves = st.integers(min_value=1, max_value=6)
pitches = st.builds(lambda name, octave: f"{name}{octave}", pitch_classes, octaves)
intervals = st.sampled_from(
    ["m2", "M2", "m3", "M3", "P4", "A4", "d5", "P5", "m6", "M6", "m7", "M7", "P8"]
)
scale_types = st.sampled_from(SCALE_TYPES)

# The intervals stacked on the root for some of the chord qualities we name.
STACKS = {
    "major": ("M3", "P5"),
    "minor": ("m3", "P5"),
    "diminished": ("m3", "d5"),
    "dominant7": ("M3", "P5", "m7"),
    "major7": ("M3", "P5", "M7"),
    "minor7": ("m3", "P5", "m7"),
    "half_diminished7": ("m3", "d5", "m7"),
}


@given(st.lists(pitches, min_size=1, max_size=6), intervals)
def test_transpose_up_then_down_returns_the_original(notes, interval):
    up = transpose(notes, interval, "up")
    assert transpose(up.pitches, interval, "down").pitches == notes


@given(st.lists(pitches, min_size=1, max_size=6), intervals)
def test_transpose_moves_every_pitch_by_the_same_distance(notes, interval):
    moved = transpose(notes, interval, "up")
    distances = {interval_between(a, b) for a, b in zip(notes, moved.pitches, strict=True)}
    assert distances == {moved.semitones}


@given(pitches, pitches)
def test_reversing_an_interval_flips_its_sign(first, second):
    there, back = get_interval(first, second), get_interval(second, first)
    assert there.semitones == -back.semitones
    assert there.name == back.name


@given(pitches, intervals)
def test_interval_names_what_transpose_applied(start, interval):
    end = transpose([start], interval).pitches[0]
    assert get_interval(start, end).name == interval


@given(pitch_classes, scale_types)
def test_a_scale_starts_on_its_root_and_never_repeats_a_note(root, scale_type):
    notes = get_scale(root, scale_type).notes
    assert notes[0] == root
    assert len(set(notes)) == len(notes)
    assert len(notes) == (5 if "pentatonic" in scale_type else 7)


@settings(max_examples=40)
@given(st.lists(pitch_classes, min_size=1, max_size=10), st.integers(min_value=1, max_value=8))
def test_detect_scales_scores_are_ranked_and_bounded(notes, limit):
    matches = detect_scales(notes, limit)
    scores = [match.score for match in matches]
    assert len(matches) == limit
    assert scores == sorted(scores, reverse=True)
    assert all(0 <= score <= 1 for score in scores)
    assert all(set(match.outside) <= set(notes) for match in matches)


@settings(max_examples=40)
@given(st.lists(st.tuples(pitch_classes, octaves), min_size=1, max_size=8))
def test_detect_scales_ignores_octaves(notes):
    with_octaves = [f"{name}{octave}" for name, octave in notes]
    without = [name for name, _ in notes]
    summary = [(m.scale.root, m.scale.type, m.score) for m in detect_scales(with_octaves)]
    assert summary == [(m.scale.root, m.scale.type, m.score) for m in detect_scales(without)]


@given(pitch_classes, st.sampled_from(sorted(STACKS)), st.integers(min_value=2, max_value=4))
def test_a_stacked_chord_is_identified_by_its_root_and_quality(root, quality, octave):
    low = f"{root}{octave}"
    notes = [low, *(transpose([low], step).pitches[0] for step in STACKS[quality])]
    chord = identify_chord(notes)
    assert (chord.root, chord.quality, chord.bass) == (root, quality, low)


@given(
    pitch_classes,
    st.sampled_from(sorted(STACKS)),
    st.integers(min_value=0, max_value=3),
)
def test_inverting_a_chord_keeps_its_root_and_quality(root, quality, rotation):
    low = f"{root}3"
    notes = [low, *(transpose([low], step).pitches[0] for step in STACKS[quality])]
    # Move the lowest notes up an octave, one at a time, to invert the chord.
    for _ in range(rotation % len(notes)):
        notes = [*notes[1:], transpose([notes[0]], "P8").pitches[0]]
    chord = identify_chord(notes)
    assert (chord.root, chord.quality) == (root, quality)
    assert chord.bass == notes[0]
