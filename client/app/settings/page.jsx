'use client'

import React, { useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import Link from 'next/link'
import ThemeSwitcher from '../components/ThemeSwitcher.jsx'
import { useTheme } from '../contexts/ThemeContext.jsx'
import { apiBase, authHeaders, LANGUAGE_OPTIONS } from '../../lib/api'
import './settings.css'

const PERSONA_OPTIONS = [
  { value: 'child', label: 'Child' },
  { value: 'teen', label: 'Teen' },
  { value: 'adult', label: 'Adult' },
]

export default function SettingsPage() {
  const { data: session, status } = useSession()
  const { theme, setTheme, themes } = useTheme()
  const token = session?.accessToken
  const [language, setLanguage] = useState('en')
  const [persona, setPersona] = useState('adult')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [personaSource, setPersonaSource] = useState('default')

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
        if (u?.preferred_persona) setPersona(u.preferred_persona)
        if (u?.persona_source) setPersonaSource(u.persona_source)
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
      const r = await fetch(`${base}/api/auth/me`, {
        method: 'PATCH',
        headers: authHeaders(token),
        body: JSON.stringify({
          preferred_language: language,
          preferred_persona: persona,
          preferred_theme: theme,
        }),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.error || r.statusText)
      setMessage('Saved.')
    } catch (err) {
      setError(err.message || 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  if (status === 'loading' || loading) {
    return (
      <div className="settings-page">
        <p className="settings-muted">Loading…</p>
      </div>
    )
  }

  if (status === 'unauthenticated' || !token) {
    return (
      <div className="settings-page">
        <h1 className="settings-title">Settings</h1>
        <p className="settings-muted">Sign in to manage your preferences.</p>
        <Link href="/login" className="settings-link">
          Sign in
        </Link>
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

        <label className="settings-label" htmlFor="pref-persona">
          Default persona
        </label>
        {personaSource === 'google' && (
          <p className="settings-hint">
            This was inferred from your Google account birthday. Choosing a different option below switches you to manual
            control (and hides the persona bar in chat).
          </p>
        )}
        <select
          id="pref-persona"
          className="settings-select"
          value={persona}
          onChange={(e) => setPersona(e.target.value)}
        >
          {PERSONA_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>

        <div className="settings-theme-block">
          <span className="settings-label">Theme</span>
          <p className="settings-hint">Applies across the app. Saved on this device; use Save below to sync theme to your account.</p>
          <ThemeSwitcher />
        </div>

        {error && <p className="settings-error">{error}</p>}
        {message && <p className="settings-success">{message}</p>}

        <button type="submit" className="settings-save" disabled={saving}>
          {saving ? 'Saving…' : 'Save preferences'}
        </button>
      </form>
    </div>
  )
}
