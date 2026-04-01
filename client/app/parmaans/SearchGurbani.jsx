'use client'

import React, { useState, useEffect, useRef } from 'react'
import { apiBase } from '../../lib/api'

const SEARCH_MODES = [
  { value: 'auto', label: 'Auto (first letters + full text)' },
  { value: 'first_letter', label: 'First letter each word' },
  { value: 'text', label: 'Full text' },
]

export default function SearchGurbani({ onSelectShabad }) {
  const base = apiBase()
  const [query, setQuery] = useState('')
  const [searchMode, setSearchMode] = useState('auto')
  const [results, setResults] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  
  // Ref to track latest fetch to avoid race conditions
  const latestFetchId = useRef(0)

  useEffect(() => {
    const q = query.trim()
    const minLen = searchMode === 'text' ? 3 : 2
    if (q.length < minLen) {
      setResults([])
      setIsLoading(false)
      setError('')
      return
    }

    // Debounce ~300ms
    const timerId = setTimeout(async () => {
      const currentFetchId = ++latestFetchId.current
      setIsLoading(true)
      setError('')

      try {
        const params = new URLSearchParams()
        params.set('q', q)
        if (searchMode !== 'auto') params.set('mode', searchMode)
        const fetchUrl = `${base}/api/search?${params.toString()}`

        const res = await fetch(fetchUrl)
        if (!res.ok) {
          throw new Error('Search failed')
        }

        const data = await res.json()
        
        // Only update state if this is still the most recent request
        if (currentFetchId === latestFetchId.current) {
          setResults(data.results || [])
        }
      } catch (err) {
        if (currentFetchId === latestFetchId.current) {
          setError(err.message || 'An error occurred')
          setResults([])
        }
      } finally {
        if (currentFetchId === latestFetchId.current) {
          setIsLoading(false)
        }
      }
    }, 300)

    return () => clearTimeout(timerId)
  }, [query, base, searchMode])

  return (
    <div className="search-gurbani-container">
      <form 
        className="parmaans-search-form" 
        onSubmit={(e) => e.preventDefault()}
      >
        <select
          className="parmaans-search-mode"
          value={searchMode}
          onChange={(e) => setSearchMode(e.target.value)}
          aria-label="Search mode"
        >
          {SEARCH_MODES.map((m) => (
            <option key={m.value} value={m.value}>
              {m.label}
            </option>
          ))}
        </select>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Gurmukhi or Roman first letters (e.g. ੲਤਮਪ, stmp) or full words…"
          aria-label="Live search Gurbani"
        />
        {isLoading && <span style={{ padding: '0.65rem', color: 'var(--text-secondary)' }}>Loading...</span>}
      </form>

      {error && <div className="parmaans-error">{error}</div>}

      {results.length > 0 && (
        <ul className="shabad-grid">
          {results.map((s) => (
            <li key={s.id}>
              <button 
                type="button" 
                className="shabad-card-btn" 
                onClick={() => onSelectShabad?.(s)}
              >
                {/* Line 1: Gurmukhi */}
                <span className="gurmukhi">{s.gurmukhi}</span>
                
                {/* Line 2: Romanized */}
                {s.transliteration && <span className="roman">{s.transliteration}</span>}
                
                {/* Line 3: English */}
                <span className="eng">{s.translation}</span>
                
                {/* Metadata Breadcrumb */}
                <span className="meta">
                  {s.source || 'Unknown Source'} 
                  {s.verse_count && ` • ${s.verse_count} lines`}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {query.trim().length >= (searchMode === 'text' ? 3 : 2) && !isLoading && results.length === 0 && !error && (
        <p style={{ color: 'var(--text-secondary)' }}>No matches found.</p>
      )}
    </div>
  )
}
