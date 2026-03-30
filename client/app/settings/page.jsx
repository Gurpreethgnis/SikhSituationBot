'use client'

import React, { useEffect, useState } from 'react'
import { useSession, signOut, update as updateSession } from 'next-auth/react'
import Link from 'next/link'
import ThemeSwitcher from '../components/ThemeSwitcher.jsx'
import { useTheme } from '../contexts/ThemeContext.jsx'
import { apiBase, authHeaders, LANGUAGE_OPTIONS } from '../../lib/api'
import './settings.css'

export default function SettingsPage() {
  const { data: session, status } = useSession()
  const { theme, setTheme, themes } = useTheme()
  const token = session?.accessToken
  const [language, setLanguage] = useState('en')
  const [birthYear, setBirthYear] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [memoryEnabled, setMemoryEnabled] = useState(true)
  const [memoryRetentionDays, setMemoryRetentionDays] = useState(90)
  const [memories, setMemories] = useState([])
  const [memoriesOpen, setMemoriesOpen] = useState(false)
  const [memoriesLoading, setMemoriesLoading] = useState(false)

  const base = apiBase()

  useEffect(() => {
    if (status === 'unauthenticated') {
      setLoading(false)
      return
    }
    if (!token) {
      if (status === 'authenticated') setLoading(false)
      return
    }
    let cancelled = false
    ;(async () => {
      try {
        const r = await fetch(`${base}/api/auth/me`, { headers: authHeaders(token) })
        const d = await r.json()
        if (!r.ok) throw new Error(d.error || r.statusText)
        if (cancelled) return
        const u = d.user
        if (u?.preferred_language) setLanguage(u.preferred_language)
        if (u?.birth_year != null) setBirthYear(String(u.birth_year))
        if (typeof u?.memory_enabled === 'boolean') setMemoryEnabled(u.memory_enabled)
        if (u?.memory_retention_days != null) setMemoryRetentionDays(Number(u.memory_retention_days) || 90)
        if (u?.preferred_theme && themes.some((t) => t.id === u.preferred_theme)) {
          setTheme(u.preferred_theme)
        }
        setError('')
      } catch (e) {
        if (!cancelled) setError(e.message || 'Could not load settings')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [token, status, base, themes, setTheme])

  const handleSave = async (e) => {
    e.preventDefault()
    if (!token) return
    setSaving(true)
    setMessage('')
    setError('')
    try {
      const nowY = new Date().getFullYear()
      const y = parseInt(birthYear, 10)
      if (!Number.isFinite(y) || y < 1900 || y > nowY) {
        throw new Error(`Enter a valid birth year (1900–${nowY}).`)
      }
      const r = await fetch(`${base}/api/auth/me`, {
        method: 'PATCH',
        headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          preferred_language: language,
          birth_year: y,
          preferred_theme: theme,
          memory_enabled: memoryEnabled,
          memory_retention_days: memoryRetentionDays,
        }),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.error || r.statusText)
      await updateSession({ birthYearComplete: true })
      setMessage('Saved.')
    } catch (err) {
      setError(err.message || 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  const loadMemories = async () => {
    if (!token) return
    setMemoriesLoading(true)
    setError('')
    try {
      const r = await fetch(`${base}/api/memory`, { headers: authHeaders(token) })
      const d = await r.json()
      if (!r.ok) throw new Error(d.error || r.statusText)
      setMemories(d.memories || [])
    } catch (e) {
      setError(e.message || 'Could not load memories')
    } finally {
      setMemoriesLoading(false)
    }
  }

  const toggleMemoriesPanel = async () => {
    const next = !memoriesOpen
    setMemoriesOpen(next)
    if (next && memories.length === 0) await loadMemories()
  }

  const deleteMemory = async (id) => {
    if (!token) return
    try {
      const r = await fetch(`${base}/api/memory/${id}`, {
        method: 'DELETE',
        headers: authHeaders(token),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.error || r.statusText)
      setMemories((prev) => prev.filter((m) => m.id !== id))
    } catch (e) {
      setError(e.message || 'Delete failed')
    }
  }

  const clearAllMemories = async () => {
    if (!token || !window.confirm('Remove all saved conversation memories? This cannot be undone.')) return
    try {
      const r = await fetch(`${base}/api/memory/clear`, {
        method: 'POST',
        headers: authHeaders(token),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.error || r.statusText)
      setMemories([])
    } catch (e) {
      setError(e.message || 'Clear failed')
    }
  }

  if (status === 'loading' || loading) {
    return (
      <div className="settings-page">
        <p className="settings-muted">Loading…</p>
      </div>
    )
  }

  if (status === 'unauthenticated') {
    const loginHref = `/login?callbackUrl=${encodeURIComponent('/settings')}`
    return (
      <div className="settings-page">
        <h1 className="settings-title">Settings</h1>
        <p className="settings-muted">Sign in to manage your preferences.</p>
        <Link href={loginHref} className="settings-link">
          Sign in
        </Link>
      </div>
    )
  }

  if (!token) {
    return (
      <div className="settings-page">
        <h1 className="settings-title">Settings</h1>
        <p className="settings-muted">
          You are signed in, but your session is not linked to the app backend yet. Signing in again will not fix this if
          the server cannot complete Google account sync.
        </p>
        <ul className="settings-sync-hint">
          <li>
            Ensure <code>FLASK_INTERNAL_API_KEY</code> is set on both the Next.js host and the Flask API, with the same
            value.
          </li>
          <li>
            Ensure <code>FLASK_API_URL</code> / <code>NEXT_PUBLIC_API_URL</code> points at your live API (not localhost
            in production).
          </li>
        </ul>
        <p className="settings-muted">Sign out, then sign in with Google again—or use email and password if you have an account.</p>
        <div className="settings-sync-actions">
          <button type="button" className="settings-save" onClick={() => signOut({ callbackUrl: '/login?callbackUrl=/settings' })}>
            Sign out
          </button>
          <Link href="/login?callbackUrl=/settings" className="settings-link">
            Go to sign in
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="settings-page">
      <div className="settings-header">
        <Link href="/chat" className="settings-back">
          ← Chat
        </Link>
        <h1 className="settings-title">Settings</h1>
      </div>

      <form className="settings-form" onSubmit={handleSave}>
        <label className="settings-label" htmlFor="pref-lang">
          Preferred response language
        </label>
        <p className="settings-hint">Used as the default when you open chat (you can still change it per session).</p>
        <select
          id="pref-lang"
          className="settings-select"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
        >
          {LANGUAGE_OPTIONS.map((o) => (
            <option key={o.code} value={o.code}>
              {o.label}
            </option>
          ))}
        </select>

        <label className="settings-label" htmlFor="pref-birth-year">
          Year of birth
        </label>
        <p className="settings-hint">
          Response style (child, teen, or adult) is chosen automatically from your age. You can change this anytime.
        </p>
        <input
          id="pref-birth-year"
          type="number"
          className="settings-select"
          inputMode="numeric"
          min={1900}
          max={new Date().getFullYear()}
          value={birthYear}
          onChange={(e) => setBirthYear(e.target.value)}
          required
          autoComplete="bday-year"
        />

        <div className="settings-theme-block">
          <span className="settings-label">Theme</span>
          <p className="settings-hint">Applies across the app. Saved on this device; use Save below to sync theme to your account.</p>
          <ThemeSwitcher />
        </div>

        <span className="settings-label">Conversation memory</span>
        <p className="settings-hint">
          When enabled, short facts you share in Guidance mode may be saved to your account so new chats can stay in context.
          Parmaan search does not use this. You can review or delete saved items anytime.
        </p>
        <label className="settings-checkbox-row">
          <input
            type="checkbox"
            checked={memoryEnabled}
            onChange={(e) => setMemoryEnabled(e.target.checked)}
          />
          <span>Remember context across new conversations</span>
        </label>
        <label className="settings-label" htmlFor="memory-retention">
          Keep memories for (days)
        </label>
        <select
          id="memory-retention"
          className="settings-select"
          value={memoryRetentionDays}
          onChange={(e) => setMemoryRetentionDays(Number(e.target.value))}
        >
          <option value={30}>30</option>
          <option value={90}>90</option>
          <option value={180}>180</option>
          <option value={365}>365</option>
        </select>

        <div className="settings-memory-actions">
          <button type="button" className="settings-secondary" onClick={toggleMemoriesPanel}>
            {memoriesOpen ? 'Hide saved memories' : 'View saved memories'}
          </button>
          {memoriesOpen && (
            <button type="button" className="settings-secondary settings-danger" onClick={clearAllMemories}>
              Clear all memories
            </button>
          )}
        </div>
        {memoriesOpen && (
          <div className="settings-memory-list" aria-live="polite">
            {memoriesLoading ? (
              <p className="settings-muted">Loading…</p>
            ) : memories.length === 0 ? (
              <p className="settings-muted">No saved memories yet.</p>
            ) : (
              <ul className="settings-memory-ul">
                {memories.map((m) => (
                  <li key={m.id} className="settings-memory-item">
                    <span className="settings-memory-type">{m.fact_type}</span>
                    <span className="settings-memory-text">{m.content}</span>
                    <button type="button" className="settings-memory-delete" onClick={() => deleteMemory(m.id)}>
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {error && <p className="settings-error">{error}</p>}
        {message && <p className="settings-success">{message}</p>}

        <button type="submit" className="settings-save" disabled={saving}>
          {saving ? 'Saving…' : 'Save preferences'}
        </button>
      </form>
    </div>
  )
}
