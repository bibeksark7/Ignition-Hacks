// risk_score.overall runs 0-100 where HIGHER IS SAFER (see CONTEXT.md), so
// grade A/B reads green, C amber, D/F terracotta. Do not invert.
//
// Kept out of RiskGauge.jsx so that file only exports a component and Vite's
// fast refresh keeps working during the build.

export function gradeTone(grade) {
  switch (grade) {
    case 'A':
    case 'B':
      return 'good'
    case 'C':
      return 'fair'
    default:
      return 'poor'
  }
}

const GRADE_WORD = {
  A: 'Low risk',
  B: 'Low risk',
  C: 'Moderate risk',
  D: 'Elevated risk',
  F: 'High risk',
}

export function gradeWord(grade) {
  return GRADE_WORD[grade] ?? 'Risk score'
}
