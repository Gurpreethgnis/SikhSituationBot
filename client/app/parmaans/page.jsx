'use client'

import React, { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { apiBase } from '../../lib/api'
import './parmaans.css'

export default function ParmaansPage() {
  const base = apiBase()
  const [categories, setCategories] = useState([])
  const [searchQ, setSearchQ] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [browse, setBrowse] = useState({ shabads: [], page: 1, total: 0, per_page: 20 })
  const [browseQ, setBrowseQ] = useState('')
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')
  const [selected, setSelected] = useState(null)
  const [similar, setSimilar] = useState([])
  const [opposite, setOpposite] = useState({ query: '', shabads: [] })
  const [tab, setTab] = useState('search')

  const loadCategories = useCallback(async () => {
    try {
      const r = await fetch(`${base}/api/parmaans/categories`)
      const d = await r.json()
      if (r.ok) setCategories(d.categories || [])
    } catch {
      /* ignore */
    }
  }, [base])

  const loadBrowse = useCallback(
    async (page = 1) => {
      setLoading(true)
      setErr('')
      try {
        const q = new URLSearchParams({ page: String(page), per_page: '20' })
        if (browseQ.trim()) q.set('q', browseQ.trim())
        const r = await fetch(`${base}/api/parmaans/browse?${q}`)
        const d = await r.json()
        if (!r.ok) throw new Error(d.error || r.statusText)
        setBrowse({
          shabads: d.shabads || [],
          page: d.page,
          total: d.total,
          per_page: d.per_page,
        })
      } catch (e) {
        setErr(e.message || 'Browse failed')
      } finally {
        setLoading(false)
      }
    },
    [base, browseQ]
  )

  useEffect(() => {
    loadCategories()
  }, [loadCategories])

  useEffect(() => {
    if (tab === 'browse') loadBrowse(1)
  }, [tab, loadBrowse])

  const runSearch = async (q) => {
    const query = (q ?? searchQ).trim()
    if (!query) return
    setLoading(true)
    setErr('')
    try {
      const r = await fetch(`${base}/api/parmaans/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, limit: 15 }),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.error || r.statusText)
      setSearchResults(d.shabads || [])
      setTab('search')
    } catch (e) {
      setErr(e.message || 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  const openShabad = async (s) => {
    setSelected(s)
    setSimilar([])
    setOpposite({ query: '', shabads: [] })
    if (!s?.id) return
    setLoading(true)
    setErr('')
    try {
      const [rs, ro] = await Promise.all([
        fetch(`${base}/api/parmaans/${s.id}/similar?limit=8`),
        fetch(`${base}/api/parmaans/${s.id}/opposite?limit=8`),
      ])
      const ds = await rs.json()
      const do_ = await ro.json()
      if (rs.ok) setSimilar(ds.shabads || [])
      if (ro.ok) setOpposite({ query: do_.query || '', shabads: do_.shabads || [] })
    } catch (e) {
      setErr(e.message || 'Could not load related Shabads')
    } finally {
      setLoading(false)
    }
  }

  const categorySearch = (cat) => {
    const q = (cat.hints || []).join(' ')
    setSearchQ(q)
    runSearch(q)
  }

  return (
    <div className="parmaans-page">
      <header className="parmaans-header">
        <div>
          <h1>Parmaan discovery</h1>
          <p className="parmaans-sub">Search, browse, and explore Gurbani with semantic similarity and contrasting themes.</p>
        </div>
        <nav className="parmaans-nav">
          <Link href="/">Home</Link>
          <Link href="/chat">Chat</Link>
        </nav>
      </header>

      <div className="parmaans-tabs">
        <button type="button" className={tab === 'search' ? 'active' : ''} onClick={() => setTab('search')}>
          Search
        </button>
        <button type="button" className={tab === 'browse' ? 'active' : ''} onClick={() => setTab('browse')}>
          Browse
        </button>
        <button type="button" className={tab === 'categories' ? 'active' : ''} onClick={() => setTab('categories')}>
          Topics
        </button>
      </div>

      {err && <div className="parmaans-error">{err}</div>}

      {tab === 'search' && (
        <section className="parmaans-panel">
          <form
            className="parmaans-search-form"
            onSubmit={(e) => {
              e.preventDefault()
              runSearch()
            }}
          >
            <input
              value={searchQ}
              onChange={(e) => setSearchQ(e.target.value)}
              placeholder="Describe a situation or theme (semantic search)…"
              aria-label="Search parmaans"
            />
            <button type="submit" disabled={loading}>
              {loading ? '…' : 'Search'}
            </button>
          </form>
          <ul className="shabad-grid">
            {searchResults.map((s) => (
              <li key={s.id}>
                <button type="button" className="shabad-card-btn" onClick={() => openShabad(s)}>
                  <span className="gurmukhi">{s.gurmukhi}</span>
                  <span className="eng">{s.english_translation}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {tab === 'browse' && (
        <section className="parmaans-panel">
          <form
            className="parmaans-search-form"
            onSubmit={(e) => {
              e.preventDefault()
              loadBrowse(1)
            }}
          >
            <input value={browseQ} onChange={(e) => setBrowseQ(e.target.value)} placeholder="Filter browse…" />
            <button type="submit" disabled={loading}>
              Apply
            </button>
          </form>
          <ul className="shabad-grid">
            {browse.shabads.map((s) => (
              <li key={s.id}>
                <button type="button" className="shabad-card-btn" onClick={() => openShabad(s)}>
                  <span className="gurmukhi">{s.gurmukhi}</span>
                  <span className="eng">{s.english_translation}</span>
                </button>
              </li>
            ))}
          </ul>
          <div className="parmaans-pager">
            <button
              type="button"
              disabled={browse.page <= 1 || loading}
              onClick={() => loadBrowse(browse.page - 1)}
            >
              Previous
            </button>
            <span>
              Page {browse.page} · {browse.total} total
            </span>
            <button
              type="button"
              disabled={browse.page * browse.per_page >= browse.total || loading}
              onClick={() => loadBrowse(browse.page + 1)}
            >
              Next
            </button>
          </div>
        </section>
      )}

      {tab === 'categories' && (
        <section className="parmaans-panel category-grid">
          {categories.map((c) => (
            <button key={c.id} type="button" className="category-tile" onClick={() => categorySearch(c)}>
              <strong>{c.label}</strong>
              <span>{(c.hints || []).slice(0, 3).join(' · ')}</span>
            </button>
          ))}
        </section>
      )}

      {selected && (
        <aside className="parmaans-detail" role="dialog" aria-label="Shabad detail">
          <button type="button" className="parmaans-close" onClick={() => setSelected(null)}>
            ×
          </button>
          <h2 className="gurmukhi-large">{selected.gurmukhi}</h2>
          {selected.romanization && <p className="roman">{selected.romanization}</p>}
          <p className="eng-large">{selected.english_translation}</p>
          {selected.source && <p className="meta">Source: {selected.source}</p>}
          {selected.sttm_link && (
            <a className="sttm-btn" href={selected.sttm_link} target="_blank" rel="noopener noreferrer">
              Open on SikhiToTheMax ↗
            </a>
          )}

          <div className="related-tabs">
            <h3>Similar</h3>
            <ul className="mini-list">
              {similar.map((s) => (
                <li key={s.id}>
                  <button type="button" onClick={() => openShabad(s)}>
                    {(s.english_translation || '').length > 80
                      ? `${(s.english_translation || '').slice(0, 80)}…`
                      : s.english_translation || s.gurmukhi}
                  </button>
                </li>
              ))}
            </ul>
            <h3>Contrasting / complementary</h3>
            {opposite.query && <p className="opposite-q">Theme probe: {opposite.query}</p>}
            <ul className="mini-list">
              {opposite.shabads.map((s) => (
                <li key={s.id}>
                  <button type="button" onClick={() => openShabad(s)}>
                    {(s.english_translation || '').length > 80
                      ? `${(s.english_translation || '').slice(0, 80)}…`
                      : s.english_translation || s.gurmukhi}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </aside>
      )}
    </div>
  )
}
