import { chordSymbol, pretty, TOOL_LABELS, words } from "../format";
import type { Analysis, Chord, Interval, Progression, Scale, ScaleMatch, Transposition } from "../types";

function Notes({ notes }: { notes: string[] }) {
  return (
    <div className="chips">
      {notes.map((note, index) => (
        <span key={index} className="chip">
          {pretty(note)}
        </span>
      ))}
    </div>
  );
}

function ChordView({ chord }: { chord: Chord }) {
  return (
    <>
      <div className="headline">{chordSymbol(chord)}</div>
      <p className="detail">
        {pretty(chord.root)} {words(chord.quality)}
        {chord.bass && `, ${pretty(chord.bass)} in the bass`}
      </p>
      <Notes notes={chord.pitches} />
    </>
  );
}

function ScaleView({ scale }: { scale: Scale }) {
  return (
    <>
      <div className="headline">
        {pretty(scale.root)} {words(scale.type)}
      </div>
      <Notes notes={scale.notes} />
    </>
  );
}

function MatchesView({ matches }: { matches: ScaleMatch[] }) {
  return (
    <ol className="matches">
      {matches.map((match, index) => (
        <li key={index} className={index === 0 ? "best" : undefined}>
          <span className="match-name">
            {pretty(match.scale.root)} {words(match.scale.type)}
          </span>
          <span className="meter" aria-hidden="true">
            <span style={{ width: `${Math.round(match.score * 100)}%` }} />
          </span>
          <span className="match-score">{match.score.toFixed(2)}</span>
          {match.outside.length > 0 && (
            <span className="outside">outside: {match.outside.map(pretty).join(", ")}</span>
          )}
        </li>
      ))}
    </ol>
  );
}

function IntervalView({ interval }: { interval: Interval }) {
  const count = Math.abs(interval.semitones);
  return (
    <>
      <div className="headline">{interval.description}</div>
      <p className="detail">
        {interval.name}, {count} {count === 1 ? "semitone" : "semitones"} {interval.direction}
      </p>
    </>
  );
}

function TranspositionView({ result }: { result: Transposition }) {
  return (
    <>
      <div className="headline">
        {result.direction === "up" ? "Up" : "Down"} {result.interval}
      </div>
      <p className="detail">{Math.abs(result.semitones)} semitones</p>
      <Notes notes={result.pitches} />
    </>
  );
}

function ProgressionView({ progression }: { progression: Progression }) {
  const landings = new Map(progression.cadences.map((cadence) => [cadence.index, cadence.type]));
  return (
    <>
      <div className="headline">
        {pretty(progression.key.tonic)} {progression.key.mode}
      </div>
      <p className="detail">{progression.key_detected ? "Key detected from the chords" : "Key as given"}</p>
      <div className="progression">
        {progression.chords.map((entry, index) => (
          <div key={index} className={`step ${landings.has(index) ? "landing" : ""}`}>
            <span className="roman">{entry.roman}</span>
            <span className="symbol">{chordSymbol(entry.chord)}</span>
            {landings.has(index) && <span className="cadence">{landings.get(index)} cadence</span>}
          </div>
        ))}
      </div>
    </>
  );
}

function Body({ analysis }: { analysis: Analysis }) {
  const { tool, summary } = analysis;
  switch (tool) {
    case "identify_chord":
      return <ChordView chord={summary as Chord} />;
    case "get_scale":
      return <ScaleView scale={summary as Scale} />;
    case "detect_scales":
      return <MatchesView matches={summary as ScaleMatch[]} />;
    case "get_interval":
      return <IntervalView interval={summary as Interval} />;
    case "transpose":
      return <TranspositionView result={summary as Transposition} />;
    case "analyze_progression":
      return <ProgressionView progression={summary as Progression} />;
    default:
      return <pre>{JSON.stringify(summary, null, 2)}</pre>;
  }
}

/** A structured view of the latest tool result. */
export function AnalysisPanel({ analysis }: { analysis: Analysis | null }) {
  return (
    <div className="card analysis">
      <div className="card-head">
        <div className="label">Analysis</div>
        {analysis && <div className="label muted">{TOOL_LABELS[analysis.tool] ?? analysis.tool}</div>}
      </div>
      {analysis ? <Body analysis={analysis} /> : <p className="hint">The latest result appears here.</p>}
    </div>
  );
}
