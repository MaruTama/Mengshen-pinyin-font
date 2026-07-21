import { useRef, useState } from 'react'

/**
 * Search-box query state that debounces into a query used for data fetching,
 * paired with a page number that resets to 1 whenever the debounced query changes.
 */
export function useDebouncedPagedSearch(delayMs = 300) {
  const [query, setQueryState] = useState('')
  const [debounced, setDebounced] = useState('')
  const [page, setPage] = useState(1)
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  const setQuery = (value: string) => {
    setQueryState(value)
    clearTimeout(timer.current)
    timer.current = setTimeout(() => {
      setDebounced(value)
      setPage(1)
    }, delayMs)
  }

  return { query, setQuery, debounced, page, setPage }
}
