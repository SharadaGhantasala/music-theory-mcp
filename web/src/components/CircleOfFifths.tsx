import { pretty } from "../format";
import type { KeyFocus } from "../keys";

// Major keys clockwise from C, with their relative minors on the inner ring.
const MAJORS = ["C", "G", "D", "A", "E", "B", "F#", "Db", "Ab", "Eb", "Bb", "F"];
const MINORS = ["Am", "Em", "Bm", "F#m", "C#m", "G#m", "Ebm", "Bbm", "Fm", "Cm", "Gm", "Dm"];
// Pitch class of each major key above, in the same order.
const MAJOR_CLASSES = [0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5];

const SIZE = 240;
const CENTRE = SIZE / 2;
const OUTER = 104;
const INNER = 70;
const HUB = 40;

function point(index: number, radius: number): [number, number] {
  const angle = (index / 12) * 2 * Math.PI - Math.PI / 2;
  return [CENTRE + radius * Math.cos(angle), CENTRE + radius * Math.sin(angle)];
}

/** The circle of fifths, drawn in thin radial lines, with the current key lit. */
export function CircleOfFifths({ focus }: { focus: KeyFocus | null }) {
  // A minor key sits on the inner ring, under its relative major three semitones up.
  const litIndex = focus
    ? MAJOR_CLASSES.indexOf(focus.minor ? (focus.tonic + 3) % 12 : focus.tonic)
    : -1;

  return (
    <div className="card circle">
      <div className="card-head">
        <div className="label">Key</div>
        {focus && <div className="label muted">{pretty(focus.label)}</div>}
      </div>
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} role="img" aria-label={focus ? `Circle of fifths, ${focus.label} highlighted` : "Circle of fifths"}>
        {MAJORS.map((_, index) => {
          const [x1, y1] = point(index + 0.5, HUB);
          const [x2, y2] = point(index + 0.5, OUTER + 18);
          return <line key={index} x1={x1} y1={y1} x2={x2} y2={y2} className="spoke" />;
        })}
        <circle cx={CENTRE} cy={CENTRE} r={HUB} className="ring" />
        <circle cx={CENTRE} cy={CENTRE} r={(OUTER + INNER) / 2 + 2} className="ring" />
        {litIndex >= 0 && (
          <line
            x1={point(litIndex, HUB)[0]}
            y1={point(litIndex, HUB)[1]}
            x2={point(litIndex, focus?.minor ? INNER - 14 : OUTER - 14)[0]}
            y2={point(litIndex, focus?.minor ? INNER - 14 : OUTER - 14)[1]}
            className="spoke lit"
          />
        )}
        {MAJORS.map((name, index) => {
          const [x, y] = point(index, OUTER);
          const lit = index === litIndex && !focus?.minor;
          return (
            <g key={name} className={lit ? "key lit" : "key"}>
              {lit && <circle cx={x} cy={y} r={14} />}
              <text x={x} y={y} dy="0.35em" textAnchor="middle">
                {pretty(name)}
              </text>
            </g>
          );
        })}
        {MINORS.map((name, index) => {
          const [x, y] = point(index, INNER);
          const lit = index === litIndex && Boolean(focus?.minor);
          return (
            <g key={name} className={lit ? "key minor lit" : "key minor"}>
              {lit && <circle cx={x} cy={y} r={14} />}
              <text x={x} y={y} dy="0.35em" textAnchor="middle">
                {pretty(name)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
