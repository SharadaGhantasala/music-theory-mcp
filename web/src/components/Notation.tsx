import { OpenSheetMusicDisplay } from "opensheetmusicdisplay";
import { useEffect, useRef, useState } from "react";
import * as Tone from "tone";

import { fetchMusicXml, fetchScoreEvents, midiUrl } from "../api";

const BEAT_SECONDS = 0.6;

// Tone.js writes sharps as "#" and flats as "b", which matches our pitch strings.
type Props = { artifactId: string | null };

/** The sheet-music panel: draws the current score and plays it back. */
export function Notation({ artifactId }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const display = useRef<OpenSheetMusicDisplay | null>(null);
  const synth = useRef<Tone.PolySynth | null>(null);
  const stopTimer = useRef<number | null>(null);
  const [events, setEvents] = useState<string[][]>([]);
  const [problem, setProblem] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);

  const stop = () => {
    synth.current?.releaseAll();
    synth.current?.dispose();
    synth.current = null;
    if (stopTimer.current !== null) window.clearTimeout(stopTimer.current);
    stopTimer.current = null;
    setPlaying(false);
  };

  useEffect(() => {
    if (!artifactId || !container.current) return;
    let cancelled = false;
    stop();
    setProblem(null);

    if (!display.current) {
      display.current = new OpenSheetMusicDisplay(container.current, {
        autoResize: true,
        backend: "svg",
        drawTitle: false,
        drawSubtitle: false,
        drawComposer: false,
        drawPartNames: false,
      });
    }
    const osmd = display.current;

    Promise.all([fetchMusicXml(artifactId), fetchScoreEvents(artifactId)])
      .then(async ([xml, notes]) => {
        if (cancelled) return;
        await osmd.load(xml);
        if (cancelled) return;
        osmd.render();
        setEvents(notes);
      })
      .catch((error: unknown) => {
        if (!cancelled) setProblem(error instanceof Error ? error.message : String(error));
      });

    return () => {
      cancelled = true;
    };
  }, [artifactId]);

  useEffect(() => stop, []);

  const play = async () => {
    if (playing) {
      stop();
      return;
    }
    // Browsers only allow sound after a click, which is what this is.
    await Tone.start();
    const voice = new Tone.PolySynth(Tone.Synth, {
      oscillator: { type: "triangle" },
      envelope: { attack: 0.01, decay: 0.2, sustain: 0.4, release: 0.6 },
    }).toDestination();
    synth.current = voice;

    const start = Tone.now() + 0.05;
    events.forEach((pitches, index) => {
      voice.triggerAttackRelease(pitches, BEAT_SECONDS * 0.9, start + index * BEAT_SECONDS);
    });
    setPlaying(true);
    stopTimer.current = window.setTimeout(stop, (events.length * BEAT_SECONDS + 0.8) * 1000);
  };

  return (
    <div className="card notation">
      <div className="card-head">
        <div className="label">Notation</div>
        {artifactId && (
          <div className="actions">
            <a className="ghost" href={midiUrl(artifactId)}>
              MIDI
            </a>
            <button className="primary" onClick={play} disabled={events.length === 0}>
              {playing ? "Stop" : "Play"}
            </button>
          </div>
        )}
      </div>
      {!artifactId && <p className="hint">Scores appear here when a tool draws one.</p>}
      {problem && (
        <p className="problem" role="alert">
          {problem}
        </p>
      )}
      <div ref={container} className="score" />
    </div>
  );
}
