// Higher risk_score.overall = safer (matches the credit-score-style framing
// in CONTEXT.md), so grade A/B are green, C is amber, D/F are red.
function gradeColor(grade) {
  switch (grade) {
    case 'A':
    case 'B':
      return 'var(--canopy)'
    case 'C':
      return 'var(--frame)'
    default:
      return 'var(--brick)'
  }
}

export default function RiskGauge({ score, grade }) {
  const pct = Math.max(0, Math.min(100, score ?? 0))
  const color = gradeColor(grade)

  return (
    <div
      className="gauge"
      style={{ background: `conic-gradient(${color} ${pct * 3.6}deg, var(--border) 0deg)` }}
      role="img"
      aria-label={`Risk score ${Math.round(pct)} out of 100, grade ${grade ?? '?'}`}
    >
      <div className="gauge-inner">
        <div className="gauge-score">{Math.round(pct)}</div>
        {grade && <div className="gauge-grade">{grade}</div>}
      </div>
    </div>
  )
}
