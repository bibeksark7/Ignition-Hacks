import { useEffect, useRef, useState } from 'react'

/* Motion primitives.
 *
 * Everything here is transform/opacity only and every hook no-ops under
 * prefers-reduced-motion, so the page still works as a static document for
 * anyone who has asked for that - which on a page about insurance risk is a
 * real slice of the audience, not a checkbox.
 */

export function prefersReducedMotion() {
  return typeof window !== 'undefined'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/* Reveal on first scroll into view.
 *
 * Fires once and then unobserves - content that re-animates every time it
 * crosses the viewport is the thing that makes scroll-driven pages feel
 * cheap rather than considered. */
export function useReveal(options = {}) {
  const { threshold = 0.15, rootMargin = '0px 0px -8% 0px' } = options
  const ref = useRef(null)
  const [shown, setShown] = useState(() => prefersReducedMotion())

  useEffect(() => {
    if (prefersReducedMotion()) return
    const node = ref.current
    if (!node) return

    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setShown(true)
          io.unobserve(node)
        }
      },
      { threshold, rootMargin },
    )
    io.observe(node)
    return () => io.disconnect()
  }, [threshold, rootMargin])

  return [ref, shown]
}

/* Count a number up once it is visible.
 *
 * Eased rather than linear: a linear count reads like a spinning odometer,
 * an eased one reads like the figure is settling. Currency is rounded to
 * whole dollars on the way so the last frames don't flicker cents. */
export function useCountUp(value, { duration = 900, decimals = 0 } = {}) {
  const [display, setDisplay] = useState(() => (prefersReducedMotion() ? value : null))
  const [ref, shown] = useReveal({ threshold: 0.4 })
  const started = useRef(false)

  useEffect(() => {
    if (value == null) return
    if (prefersReducedMotion()) { setDisplay(value); return }
    if (!shown || started.current) return
    started.current = true

    const from = 0
    const t0 = performance.now()
    let raf = 0

    const step = (now) => {
      const t = Math.min(1, (now - t0) / duration)
      // easeOutExpo - moves fast, then settles rather than stopping dead
      const eased = t === 1 ? 1 : 1 - Math.pow(2, -10 * t)
      const current = from + (value - from) * eased
      setDisplay(decimals ? Number(current.toFixed(decimals)) : Math.round(current))
      if (t < 1) raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [value, shown, duration, decimals])

  return [ref, display ?? value]
}

/* Magnetic pull toward the pointer.
 *
 * The element leans a few pixels toward the cursor while it is nearby and
 * springs back on leave. Kept deliberately small - past about 10px it stops
 * feeling responsive and starts feeling like the button is dodging you. */
export function useMagnetic(strength = 0.28, maxOffset = 10) {
  const ref = useRef(null)

  useEffect(() => {
    if (prefersReducedMotion()) return
    const node = ref.current
    if (!node) return
    if (!window.matchMedia('(pointer: fine)').matches) return

    const onMove = (e) => {
      const r = node.getBoundingClientRect()
      const dx = e.clientX - (r.left + r.width / 2)
      const dy = e.clientY - (r.top + r.height / 2)
      const x = Math.max(-maxOffset, Math.min(maxOffset, dx * strength))
      const y = Math.max(-maxOffset, Math.min(maxOffset, dy * strength))
      node.style.transform = `translate3d(${x}px, ${y}px, 0)`
    }
    const onLeave = () => { node.style.transform = '' }

    node.addEventListener('pointermove', onMove)
    node.addEventListener('pointerleave', onLeave)
    return () => {
      node.removeEventListener('pointermove', onMove)
      node.removeEventListener('pointerleave', onLeave)
    }
  }, [strength, maxOffset])

  return ref
}
