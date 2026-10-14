import type { Chord } from "./types";

const QUALITY_SUFFIX: Record<string, string> = {
  major: "",
  minor: "m",
  diminished: "°",
  augmented: "+",
  dominant7: "7",
  major7: "maj7",
  minor7: "m7",
  half_diminished7: "ø7",
  diminished7: "°7",
  sus2: "sus2",
  sus4: "sus4",
};

/** Write flats and sharps with their music symbols: "Bb" becomes "B♭". */
export function pretty(note: string): string {
  return note.replace(/([A-G])(bb|b|##|#)/g, (_, letter: string, accidental: string) => {
    const symbols: Record<string, string> = { b: "♭", bb: "𝄫", "#": "♯", "##": "𝄪" };
    return letter + symbols[accidental];
  });
}

/** A chord symbol such as "Cmaj7" or "C/E" for an inversion. */
export function chordSymbol(chord: Chord): string {
  const symbol = pretty(chord.root) + (QUALITY_SUFFIX[chord.quality] ?? ` ${chord.quality}`);
  const bass = chord.bass?.replace(/-?\d+$/, "");
  return bass && bass !== chord.root ? `${symbol}/${pretty(bass)}` : symbol;
}

/** "natural_minor" becomes "natural minor". */
export function words(value: string): string {
  return value.replace(/_/g, " ");
}

export const TOOL_LABELS: Record<string, string> = {
  identify_chord: "Identify chord",
  get_scale: "Scale lookup",
  detect_scales: "Detect scale",
  get_interval: "Interval",
  transpose: "Transpose",
  analyze_progression: "Analyze progression",
};
