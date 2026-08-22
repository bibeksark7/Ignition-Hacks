import { useEffect, useState } from 'react'

/* Theme.
 *
 * Two grounds carrying the same pastels: LIGHT is a lilac wash, DARK is deep
 * plum. Not an inversion - each accent is re-picked for its ground, because a
 * pastel keeps its light value and reads muddy on a dark surface unless it is
 * lifted.
 *
 * Stored, because a person who picks one has told us something and being asked
 * again on the next page load is the interface forgetting.
 */

const KEY = 'sightline-theme'

export function useTheme() {
  const [theme, setTheme] = useState(() => {
    if (typeof window === 'undefined') return 'light'
    const saved = window.localStorage.getItem(KEY)
    if (saved === 'light' || saved === 'dark') return saved
    // No stored choice: follow the OS rather than assuming.
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try {
      window.localStorage.setItem(KEY, theme)
    } catch {
      /* private browsing - the choice still applies for this session */
    }
  }, [theme])

  return [theme, () => setTheme((t) => (t === 'light' ? 'dark' : 'light'))]
}
