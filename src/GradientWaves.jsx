import { useEffect, useRef } from 'react'

/* Gradient waves.
 *
 * Slow horizontal bands drifting behind the entry screen, drawn on a canvas
 * rather than with CSS gradients so the crests actually move independently
 * instead of the whole sheet sliding.
 *
 * Colours come from the palette tokens, read at mount, so this follows the
 * theme instead of hardcoding a second copy of the palette.
 *
 * Deliberately cheap: five strokes on a half-resolution buffer, and it stops
 * entirely when the tab is hidden or the user asked for reduced motion. This
 * sits under the first thing a judge sees, so it must never be the reason the
 * page feels slow.
 */

const BANDS = [
  { token: '--water', amp: 0.055, speed: 0.00022, phase: 0.0, y: 0.44, width: 1.7 },
  { token: '--wind', amp: 0.075, speed: -0.00017, phase: 1.7, y: 0.52, width: 2.1 },
  { token: '--canopy', amp: 0.05, speed: 0.00013, phase: 3.1, y: 0.61, width: 1.5 },
  { token: '--accent', amp: 0.09, speed: -0.0001, phase: 4.6, y: 0.7, width: 2.6 },
  { token: '--water', amp: 0.065, speed: 0.00008, phase: 5.9, y: 0.79, width: 1.9 },
]

export default function GradientWaves() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const styles = getComputedStyle(document.documentElement)
    const colours = BANDS.map((b) => styles.getPropertyValue(b.token).trim() || '#47dce2')

    // Half resolution: these are soft blurred bands, so the extra pixels buy
    // nothing and cost fill rate on the one screen that must feel instant.
    const DPR = Math.min(window.devicePixelRatio || 1, 2) * 0.5
    let width = 0
    let height = 0

    const resize = () => {
      const rect = canvas.getBoundingClientRect()
      width = Math.max(1, Math.floor(rect.width * DPR))
      height = Math.max(1, Math.floor(rect.height * DPR))
      canvas.width = width
      canvas.height = height
    }
    resize()

    let frame = 0
    const draw = (t) => {
      ctx.clearRect(0, 0, width, height)
      ctx.globalCompositeOperation = 'lighter'

      BANDS.forEach((band, i) => {
        ctx.beginPath()
        const baseY = height * band.y
        const amp = height * band.amp
        // Two summed sines at different rates, so the crest never repeats on a
        // visible period and the motion does not read as a loop.
        for (let x = 0; x <= width; x += 6) {
          const p = (x / width) * Math.PI * band.width + band.phase
          const y =
            baseY +
            Math.sin(p + t * band.speed) * amp +
            Math.sin(p * 1.9 - t * band.speed * 1.6) * amp * 0.35
          if (x === 0) ctx.moveTo(x, y)
          else ctx.lineTo(x, y)
        }
        ctx.lineTo(width, height)
        ctx.lineTo(0, height)
        ctx.closePath()

        const g = ctx.createLinearGradient(0, baseY - amp, 0, height)
        g.addColorStop(0, hexToRgba(colours[i], 0.24))
        g.addColorStop(1, hexToRgba(colours[i], 0))
        ctx.fillStyle = g
        ctx.fill()
      })

      ctx.globalCompositeOperation = 'source-over'
      if (!reduced) frame = requestAnimationFrame(draw)
    }

    frame = requestAnimationFrame(draw)

    // A background animation has no business running against a tab nobody is
    // looking at.
    const onVisibility = () => {
      cancelAnimationFrame(frame)
      if (!document.hidden && !reduced) frame = requestAnimationFrame(draw)
    }

    window.addEventListener('resize', resize)
    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('resize', resize)
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [])

  return <canvas className="waves" ref={canvasRef} aria-hidden="true" />
}

/* Tokens are hex; canvas gradients need alpha. */
function hexToRgba(hex, alpha) {
  const h = hex.replace('#', '')
  const full = h.length === 3 ? h.split('').map((c) => c + c).join('') : h
  const n = parseInt(full, 16)
  if (Number.isNaN(n)) return `rgba(71, 220, 226, ${alpha})`
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`
}
