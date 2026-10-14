import { OpenSheetMusicDisplay } from "opensheetmusicdisplay";
import { useEffect, useRef, useState } from "react";
import * as Tone from "tone";

import { fetchMusicXml, fetchScoreEvents, midiUrl } from "../api";

const BEAT_SECONDS = 0.6;

type Props = {
  artifactId: string | null;
  // Called when someone clicks a note or chord in the score.
  onExplain: (position: number, pitches: string[]) => void;
};

/** The sheet-music panel: draws the current score, plays it back, and makes notes clickable. */
export function Notation({ artifactId, onExplain }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const display = useRef<OpenSheetMusicDisplay | null>(null);
  const synth = useRef<Tone.PolySynth | null>(null);
  const timers = useRef<number[]>([]);
  const [events, setEvents] = useState<string[][]>([]);
  const [problem, setProblem] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [active, setActive] = useState<number | null>(null);
  const explain = useRef(onExplain);
  explain.current = onExplain;

  // Each note or chord in the score is drawn as one stave-note group, in order.
  const noteGroups = (): Element[] =>
    Array.from(container.current?.querySelectorAll("g.vf-stavenote") ?? []);

  const stop = () => {
    synth.current?.releaseAll();
    synth.current?.dispose();
    synth.current = null;
    timers.current.forEach((timer) => window.clearTimeout(timer));
    timers.current = [];
    setPlaying(false);
    setActive(null);
  };

  useEffect(() => {
    if (!artifactId || !container.current) return;
    let cancelled = false;
    stop();
    setProblem(null);
    setEvents([]);

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

  // Make every note clickable once the score is drawn, and again after a resize redraws it.
  useEffect(() => {
    const host = container.current;
    if (!host || events.length === 0) return;

    const label = (pitches: string[]) => `Explain ${pitches.join(" ")}`;
    const decorate = () => {
      noteGroups().forEach((group, index) => {
        const pitches = events[index];
        if (!pitches) return;
        group.classList.add("clickable");
        group.setAttribute("role", "button");
        group.setAttribute("tabindex", "0");
        group.setAttribute("aria-label", label(pitches));
        group.classList.toggle("active", index === active);
      });
    };
    decorate();

    const target = (event: Event) => {
      const group = (event.target as Element).closest("g.vf-stavenote");
      const index = group ? noteGroups().indexOf(group) : -1;
      return index >= 0 && events[index] ? index : -1;
    };
    const onClick = (event: MouseEvent) => {
      const index = target(event);
      if (index >= 0) explain.current(index + 1, events[index]);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      const index = target(event);
      if (index >= 0) {
        event.preventDefault();
        explain.current(index + 1, events[index]);
      }
    };
    const redraws = new MutationObserver(decorate);
    redraws.observe(host, { childList: true, subtree: true });
    host.addEventListener("click", onClick);
    host.addEventListener("keydown", onKey);
    return () => {
      redraws.disconnect();
      host.removeEventListener("click", onClick);
      host.removeEventListener("keydown", onKey);
    };
  }, [events, active]);

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
      // Light up each note or chord as it sounds.
      timers.current.push(window.setTimeout(() => setActive(index), (50 + index * BEAT_SECONDS * 1000)));
    });
    setPlaying(true);
    timers.current.push(window.setTimeout(stop, (events.length * BEAT_SECONDS + 0.8) * 1000));
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
      {artifactId && events.length > 0 && (
        <p className="hint small">Click a note or chord to ask about it.</p>
      )}
      {problem && (
        <p className="problem" role="alert">
          {problem}
        </p>
      )}
      <div ref={container} className="score" />
    </div>
  );
}
