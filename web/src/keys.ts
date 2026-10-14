import type { Analysis, Chord, Progression, Scale, ScaleMatch } from "./types";

const LETTER_CLASS: Record<string, number> = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };

/** Pitch class 0-11 of a note such as "Bb" or "F#4". */
export function pitchClass(note: string): number {
  const match = /^([A-G])(##|#|bb|b)?/.exec(note);
  if (!match) return 0;
  const shift = { "#": 1, "##": 2, b: -1, bb: -2 }[match[2] ?? ""] ?? 0;
  return (LETTER_CLASS[match[1]] + shift + 12) % 12;
}

export type KeyFocus = { tonic: number; minor: boolean; label: string };

const MINOR_SCALES = new Set([
  "natural_minor",
  "harmonic_minor",
  "melodic_minor",
  "minor_pentatonic",
  "dorian",
  "phrygian",
  "locrian",
]);
const MINOR_CHORDS = new Set(["minor", "minor7", "diminished", "half_diminished7", "diminished7"]);

/** The key or tonal centre the latest result points at, if it has one. */
export function keyOf(analysis: Analysis | null): KeyFocus | null {
  if (!analysis) return null;
  const { tool, summary } = analysis;
  const fromScale = (scale: Scale): KeyFocus => ({
    tonic: pitchClass(scale.root),
    minor: MINOR_SCALES.has(scale.type),
    label: `${scale.root} ${scale.type.replace(/_/g, " ")}`,
  });
  switch (tool) {
    case "analyze_progression": {
      const { key } = summary as Progression;
      return { tonic: pitchClass(key.tonic), minor: key.mode === "minor", label: `${key.tonic} ${key.mode}` };
    }
    case "get_scale":
      return fromScale(summary as Scale);
    case "detect_scales": {
      const best = (summary as ScaleMatch[])[0];
      return best ? fromScale(best.scale) : null;
    }
    case "identify_chord": {
      const chord = summary as Chord;
      return { tonic: pitchClass(chord.root), minor: MINOR_CHORDS.has(chord.quality), label: chord.root };
    }
    default:
      return null;
  }
}
