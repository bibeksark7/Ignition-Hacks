import { gradeTone } from './grade'

// 260 degrees of dial with the gap at the bottom, so the arc reads as a meter
// rather than a progress ring.
const R = 56
const CIRC = 2 * Math.PI * R
const TRACK = CIRC * (260 / 360)

export default function RiskGauge({ score, grade, size = 148 }) {
  const pct = Math.max(0, Math.min(100, score ?? 0))
  const tone = gradeTone(grade)
  const filled = (TRACK * pct) / 100

  return (
    <div className={`gauge gauge-${tone}`} style={{ width: size, height: size }}>
      {/* The arc is rotated inside the SVG coordinate system rather than with a
          CSS transform on the <svg>: a CSS rotation contributes to the parent's
          scrollable overflow and pushed the panel 30px wider than the gauge. */}
      <svg viewBox="0 0 140 140" width={size} height={size} aria-hidden="true">
        <g transform="rotate(140 70 70)">
          <circle
            className="gauge-track"
            cx="70"
            cy="70"
            r={R}
            strokeDasharray={`${TRACK} ${CIRC}`}
          />
          {/* Drawn from empty by a CSS keyframe rather than a mounted state
              flip, which StrictMode's double effect invocation swallowed. The
              score is the most important number on the page, so it earns one
              deliberate entrance. */}
          <circle
            className="gauge-value"
            cx="70"
            cy="70"
            r={R}
            strokeDasharray={`${filled} ${CIRC}`}
            style={{ '--gauge-circ': CIRC }}
          />
        </g>
      </svg>
      <div className="gauge-face">
        <div className="gauge-score tnum">{Math.round(pct)}</div>
        <div className="gauge-outof tnum">out of 100</div>
      </div>
      <span className="visually-hidden">
        Safety score {Math.round(pct)} out of 100, grade {grade ?? 'unknown'}. Higher is safer.
      </span>
    </div>
  )
}
