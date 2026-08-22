import { forwardRef, useEffect, useMemo, useRef } from 'react'

/* Letters that respond to pointer proximity by interpolating their variable
 * font axes - the nearer the cursor, the wider and heavier the letter.
 *
 * Adapted from the supplied component with one change: the original wrapped
 * each letter in motion.span but passed it no animation props, because all the
 * work happens through direct style writes inside a rAF loop. Plain spans do
 * exactly the same thing without pulling in a 50kB animation library.
 *
 * Needs a font with real variable axes to do anything - Archivo is loaded with
 * wdth 62..125 and wght 100..900 for this.
 */

function useAnimationFrame(callback) {
  useEffect(() => {
    let frameId
    const loop = () => {
      callback()
      frameId = requestAnimationFrame(loop)
    }
    frameId = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(frameId)
  }, [callback])
}

function useMousePositionRef(containerRef) {
  const positionRef = useRef({ x: 0, y: 0 })

  useEffect(() => {
    const update = (x, y) => {
      if (containerRef?.current) {
        const rect = containerRef.current.getBoundingClientRect()
        positionRef.current = { x: x - rect.left, y: y - rect.top }
      } else {
        positionRef.current = { x, y }
      }
    }
    const onMouse = (e) => update(e.clientX, e.clientY)
    const onTouch = (e) => {
      const t = e.touches[0]
      if (t) update(t.clientX, t.clientY)
    }
    window.addEventListener('mousemove', onMouse)
    window.addEventListener('touchmove', onTouch)
    return () => {
      window.removeEventListener('mousemove', onMouse)
      window.removeEventListener('touchmove', onTouch)
    }
  }, [containerRef])

  return positionRef
}

const VariableProximity = forwardRef(function VariableProximity(props, ref) {
  const {
    label,
    fromFontVariationSettings,
    toFontVariationSettings,
    containerRef,
    radius = 50,
    falloff = 'linear',
    className = '',
    onClick,
    style,
    ...rest
  } = props

  const letterRefs = useRef([])
  const interpolated = useRef([])
  const mouse = useMousePositionRef(containerRef)
  const last = useRef({ x: null, y: null })

  const parsed = useMemo(() => {
    const parse = (str) =>
      new Map(
        str
          .split(',')
          .map((s) => s.trim())
          .map((s) => {
            const [name, value] = s.split(' ')
            return [name.replace(/['"]/g, ''), parseFloat(value)]
          }),
      )
    const from = parse(fromFontVariationSettings)
    const to = parse(toFontVariationSettings)
    return Array.from(from.entries()).map(([axis, fromValue]) => ({
      axis,
      fromValue,
      toValue: to.get(axis) ?? fromValue,
    }))
  }, [fromFontVariationSettings, toFontVariationSettings])

  const falloffAt = (distance) => {
    const norm = Math.min(Math.max(1 - distance / radius, 0), 1)
    if (falloff === 'exponential') return norm ** 2
    if (falloff === 'gaussian') return Math.exp(-((distance / (radius / 2)) ** 2) / 2)
    return norm
  }

  useAnimationFrame(() => {
    if (!containerRef?.current) return
    const containerRect = containerRef.current.getBoundingClientRect()
    const { x, y } = mouse.current
    if (last.current.x === x && last.current.y === y) return
    last.current = { x, y }

    letterRefs.current.forEach((letterRef, index) => {
      if (!letterRef) return
      const rect = letterRef.getBoundingClientRect()
      const cx = rect.left + rect.width / 2 - containerRect.left
      const cy = rect.top + rect.height / 2 - containerRect.top
      const distance = Math.hypot(cx - x, cy - y)

      if (distance >= radius) {
        letterRef.style.fontVariationSettings = fromFontVariationSettings
        return
      }
      const f = falloffAt(distance)
      const settings = parsed
        .map(({ axis, fromValue, toValue }) => `'${axis}' ${fromValue + (toValue - fromValue) * f}`)
        .join(', ')
      interpolated.current[index] = settings
      letterRef.style.fontVariationSettings = settings
    })
  })

  const words = label.split(' ')
  let letterIndex = 0

  return (
    <span
      ref={ref}
      className={`${className} variable-proximity`}
      onClick={onClick}
      style={{ display: 'inline', ...style }}
      {...rest}
    >
      {words.map((word, wordIndex) => (
        <span key={wordIndex} style={{ display: 'inline-block', whiteSpace: 'nowrap' }}>
          {word.split('').map((letter) => {
            const i = letterIndex++
            return (
              <span
                key={i}
                ref={(el) => { letterRefs.current[i] = el }}
                style={{
                  display: 'inline-block',
                  fontVariationSettings: interpolated.current[i],
                }}
                aria-hidden="true"
              >
                {letter}
              </span>
            )
          })}
          {wordIndex < words.length - 1 && <span style={{ display: 'inline-block' }}>&nbsp;</span>}
        </span>
      ))}
      {/* The split letters are hidden from assistive tech; this carries the
          real string so the heading still reads as one sentence. */}
      <span className="visually-hidden">{label}</span>
    </span>
  )
})

export default VariableProximity
