'use client'

import React, { useState, useEffect, useRef, useMemo } from 'react'
import { apiBase } from '../../lib/api'
import { useTranslation } from '../contexts/TranslationContext.jsx'

const SEARCH_MODE_DEFS = [
  { value: 'auto', labelKey: 'parmaanLiveSearchModeAuto' },
  { value: 'first_letter', labelKey: 'parmaanLiveSearchModeFirstLetter' },
  { value: 'text', labelKey: 'parmaanLiveSearchModeText' },
]

export default function SearchGurbani({ onSelectShabad }) {
  const { t } = useTranslation()
  const searchModes = useMemo(
    () => SEARCH_MODE_DEFS.map((m) => ({ ...m, label: t(m.labelKey) })),
    [t]
  )
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
          aria-label={t('parmaanLiveSearchModeAria')}
        >
          {searchModes.map((m) => (
            <option key={m.value} value={m.value}>
              {m.label}
            </option>
          ))}
        </select>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t('parmaanLiveSearchPlaceholder')}
          aria-label={t('parmaanLiveSearchAria')}
        />
        {isLoading && (
          <span style={{ padding: '0.65rem', color: 'var(--text-secondary)' }}>{t('loading')}</span>
        )}
      </form>

      {error && <div className="parmaans-error">{error}</div>}

      {results.length > 0 && (
        <ul className="shabad-grid">
          {results.map((s) => (
            <li key={s.id}>
              <button 
                type="button" 
                className="shabad-card-btn" 
                onClick={() => onSelectShabad?.(s, { query: query.trim() })}
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
        <p style={{ color: 'var(--text-secondary)' }}>{t('parmaanLiveSearchNoMatches')}</p>
      )}
    </div>
  )
}
