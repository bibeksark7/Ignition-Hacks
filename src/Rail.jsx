import { useEffect, useState } from 'react'

/* Section rail.
 *
 * Up and down arrows that step through the report a section at a time, with a
 * dot per section showing where you are. The report is long and the figures
 * that matter are spread down it, so being able to move between them without
 * a trackpad matters - especially when someone is presenting this on a laptop
 * in front of a room.
 */

const REPORT_SECTIONS = [
  { id: 'verdict', label: 'The verdict' },
  { id: 'measurements', label: 'What we measured' },
  { id: 'cost-breakdown', label: 'Where the cost comes from' },
  { id: 'what-to-do', label: 'What to do about it' },
]

/* The entry screen steps through the same way the report does, so the control
   a person learns on the first screen still works on the second. */
export const ENTRY_SECTIONS = [
  { id: 'entry-start', label: 'Start' },
  { id: 'entry-samples', label: 'Sample locations' },
  { id: 'entry-confirm', label: 'Confirm the pin' },
]

export default function Rail({ sections = REPORT_SECTIONS }) {
  const [current, setCurrent] = useState(0)
  const [present, setPresent] = useState([])

  // Only offer steps for sections actually on the page, and track which one is
  // in view so the dots mean something.
  useEffect(() => {
    const nodes = sections.map((s) => document.getElementById(s.id)).filter(Boolean)
    setPresent(nodes.map((n) => n.id))
    if (!nodes.length) return

    const io = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((e) => e.isIntersecting)
        if (!visible.length) return
        const top = visible.reduce((a, b) => (a.intersectionRatio > b.intersectionRatio ? a : b))
        const i = sections.findIndex((s) => s.id === top.target.id)
        if (i !== -1) setCurrent(i)
      },
      { threshold: [0.25, 0.5, 0.75], rootMargin: '-15% 0px -35% 0px' },
    )
    nodes.forEach((n) => io.observe(n))
    return () => io.disconnect()
    // Re-observe when the entry screen grows a confirm step mid-flow.
  }, [sections, present.length])

  const go = (index) => {
    const clamped = Math.max(0, Math.min(sections.length - 1, index))
    const el = document.getElementById(sections[clamped].id)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  if (present.length < 2) return null

  return (
    <nav className="rail" aria-label="Jump between sections">
      <button type="button" className="rail-step" onClick={() => go(current - 1)} aria-label="Previous section">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M6 15l6-6 6 6" fill="none" stroke="currentColor" strokeWidth="1.8" />
        </svg>
      </button>

      <ul className="rail-dots">
        {sections.map((s, i) => (
          <li key={s.id}>
            <button
              type="button"
              className={`rail-dot${i === current ? ' is-current' : ''}`}
              onClick={() => go(i)}
              aria-label={s.label}
              aria-current={i === current ? 'true' : undefined}
            />
          </li>
        ))}
      </ul>

      <button type="button" className="rail-step" onClick={() => go(current + 1)} aria-label="Next section">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" strokeWidth="1.8" />
        </svg>
      </button>
    </nav>
  )
}
