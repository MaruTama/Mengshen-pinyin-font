import { useEffect, useState } from 'react'

// One FontFace per URL, shared across components
const loaded = new Map<string, Promise<string>>()
let counter = 0

function loadFont(url: string): Promise<string> {
  const existing = loaded.get(url)
  if (existing) return existing

  const family = `app-font-${counter++}`
  const promise = new FontFace(family, `url("${url}")`)
    .load()
    .then((face) => {
      document.fonts.add(face)
      return family
    })
    .catch(() => {
      loaded.delete(url)
      return ''
    })
  loaded.set(url, promise)
  return promise
}

/**
 * Load a font file and return a CSS font-family name for it
 * (undefined while loading or on failure — caller falls back).
 */
export function useFontFace(url: string | null): string | undefined {
  const [family, setFamily] = useState<string>()

  useEffect(() => {
    setFamily(undefined)
    if (!url) return
    let cancelled = false
    loadFont(url).then((name) => {
      if (!cancelled && name) setFamily(name)
    })
    return () => {
      cancelled = true
    }
  }, [url])

  return family
}
