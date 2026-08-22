import { useEffect, useRef, useState } from 'react'

/* Surveyor's reticle cursor.
 *
 * Two parts moving at different rates: a small dot pinned to the true pointer
 * position, and a larger ring that eases toward it. The lag is the whole
 * effect - the ring reads as weight being dragged around, and it settles into
 * a crosshair when you stop, which is the instrument Goad's surveyors were
 * using when they drew the plans this project is named after.
 *
 * Rules it follows:
 *   - never intercepts a click (pointer-events: none throughout)
 *   - transform-only animation, driven by one rAF loop, so it stays off the
 *     layout path and costs nothing measurable
 *   - disabled outright for coarse pointers and for reduced-motion users
 */

const RING_EASE = 0.18 // fraction of remaining distance per frame
const HOVER_SELECTOR = 'a, button, input, select, textarea, [role="button"], .layer-toggle, label'

export default function Cursor() {
  const ringRef = useRef(null)
  const dotRef = useRef(null)
  const target = useRef({ x: -100, y: -100 })
  const ring = useRef({ x: -100, y: -100 })
  const frame = useRef(0)

  const [enabled, setEnabled] = useState(false)
  const [hovering, setHovering] = useState(false)
  const [pressed, setPressed] = useState(false)
  const [visible, setVisible] = useState(false)

  // Only for users driving a real pointer who haven't asked for less motion.
  useEffect(() => {
    const fine = window.matchMedia('(pointer: fine)')
    const still = window.matchMedia('(prefers-reduced-motion: reduce)')
    const sync = () => setEnabled(fine.matches && !still.matches)
    sync()
    fine.addEventListener('change', sync)
    still.addEventListener('change', sync)
    return () => {
      fine.removeEventListener('change', sync)
      still.removeEventListener('change', sync)
    }
  }, [])

  useEffect(() => {
    if (!enabled) return

    const onMove = (e) => {
      target.current = { x: e.clientX, y: e.clientY }
      setVisible(true)
      setHovering(Boolean(e.target?.closest?.(HOVER_SELECTOR)))
    }
    const onLeave = () => setVisible(false)
    const onDown = () => setPressed(true)
    const onUp = () => setPressed(false)

    window.addEventListener('pointermove', onMove, { passive: true })
    window.addEventListener('pointerdown', onDown, { passive: true })
    window.addEventListener('pointerup', onUp, { passive: true })
    document.addEventListener('mouseleave', onLeave)

    const tick = () => {
      // The dot is exact; only the ring eases, which is what creates the lag.
      ring.current.x += (target.current.x - ring.current.x) * RING_EASE
      ring.current.y += (target.current.y - ring.current.y) * RING_EASE

      if (dotRef.current) {
        dotRef.current.style.transform =
          `translate3d(${target.current.x}px, ${target.current.y}px, 0) translate(-50%, -50%)`
      }
      if (ringRef.current) {
        ringRef.current.style.transform =
          `translate3d(${ring.current.x}px, ${ring.current.y}px, 0) translate(-50%, -50%)`
      }
      frame.current = requestAnimationFrame(tick)
    }
    frame.current = requestAnimationFrame(tick)

    return () => {
      cancelAnimationFrame(frame.current)
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerdown', onDown)
      window.removeEventListener('pointerup', onUp)
      document.removeEventListener('mouseleave', onLeave)
    }
  }, [enabled])

  if (!enabled) return null

  const state = [
    'cursor-ring',
    hovering ? 'is-hovering' : '',
    pressed ? 'is-pressed' : '',
    visible ? '' : 'is-hidden',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <>
      <div ref={ringRef} className={state} aria-hidden="true">
        <span className="cursor-tick cursor-tick-n" />
        <span className="cursor-tick cursor-tick-e" />
        <span className="cursor-tick cursor-tick-s" />
        <span className="cursor-tick cursor-tick-w" />
      </div>
      <div
        ref={dotRef}
        className={`cursor-dot${visible ? '' : ' is-hidden'}`}
        aria-hidden="true"
      />
    </>
  )
}
