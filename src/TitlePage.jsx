import { useEffect, useRef, useState } from 'react'
import VariableProximity from './VariableProximity'
import { prefersReducedMotion } from './motion'

/* Title page.
 *
 * One image, one claim, one way forward. The background is a real dark
 * basemap of Toronto rather than stock scenery, so the first thing on screen
 * is the kind of data the product actually works from.
 *
 * The copy stays at three lines on purpose: the pitch is delivered out loud
 * over this screen, and text competing with a narrator is text nobody reads.
 */

export default function TitlePage({ onEnter }) {
  const headingRef = useRef(null)
  const [drift, setDrift] = useState({ x: 0, y: 0 })

  // The map eases against the pointer, so it reads as a surface being looked
  // at rather than a picture pasted behind the words.
  useEffect(() => {
    if (prefersReducedMotion()) return
    if (!window.matchMedia('(pointer: fine)').matches) return
    const onMove = (e) => {
      setDrift({
        x: -(e.clientX / window.innerWidth - 0.5) * 26,
        y: -(e.clientY / window.innerHeight - 0.5) * 18,
      })
    }
    window.addEventListener('pointermove', onMove, { passive: true })
    return () => window.removeEventListener('pointermove', onMove)
  }, [])

  return (
    <div className="title">
      <div
        className="title-bg"
        style={{ transform: `scale(1.08) translate3d(${drift.x}px, ${drift.y}px, 0)` }}
        aria-hidden="true"
      />
      <div className="title-veil" aria-hidden="true" />

      <span className="title-mark">Sightline</span>

      <div className="title-inner">
        <h1 className="title-heading" ref={headingRef}>
          <VariableProximity
            label="Your home is already being measured."
            containerRef={headingRef}
            fromFontVariationSettings="'wght' 200"
            toFontVariationSettings="'wght' 700"
            radius={150}
            falloff="gaussian"
          />
        </h1>

        <p className="title-sub">
          Insurers price what they can see from above. Now you can see it too.
        </p>

        <button type="button" className="title-cta" onClick={onEnter}>
          <span>Look at my home</span>
          <svg viewBox="0 0 24 24" aria-hidden="true" className="title-cta-arrow">
            <path d="M4 12h15M13 6l6 6-6 6" fill="none" stroke="currentColor" strokeWidth="1.6" />
          </svg>
        </button>
      </div>
    </div>
  )
}
