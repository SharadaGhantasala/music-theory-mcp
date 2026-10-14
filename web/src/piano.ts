import * as Tone from "tone";

// Salamander Grand Piano samples (CC BY 3.0, Alexander Holm), as hosted by Tone.js.
const BASE_URL = "https://tonejs.github.io/audio/salamander/";
// One recording every three semitones; the sampler pitch-shifts the notes in between.
const SAMPLED = ["C", "D#", "F#", "A"];

let piano: Tone.Sampler | null = null;

function sampleUrls(): Record<string, string> {
  const urls: Record<string, string> = { A0: "A0.mp3", C8: "C8.mp3" };
  for (let octave = 1; octave <= 7; octave += 1) {
    for (const note of SAMPLED) {
      urls[`${note}${octave}`] = `${note.replace("#", "s")}${octave}.mp3`;
    }
  }
  return urls;
}

/** Return the piano, downloading its samples the first time it is needed. */
export async function loadPiano(): Promise<Tone.Sampler> {
  // Browsers only allow sound after a click, and this is always called from one.
  await Tone.start();
  if (!piano) {
    piano = new Tone.Sampler({ urls: sampleUrls(), baseUrl: BASE_URL, release: 1.2 }).toDestination();
  }
  await Tone.loaded();
  return piano;
}

/** Silence anything still ringing. */
export function silencePiano(): void {
  piano?.releaseAll();
}
