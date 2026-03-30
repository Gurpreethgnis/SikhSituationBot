'use client'

import React, { useEffect, useState, Suspense } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { apiBase, authHeaders } from '../../lib/api'
import '../auth.css'

function OnboardingForm() {
  const { data: session, status, update } = useSession()
  const router = useRouter()
  const params = useSearchParams()
  const callbackUrl = params.get('callbackUrl') || '/chat'
  const token = session?.accessToken

  const [year, setYear] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [checking, setChecking] = useState(true)

  const base = apiBase()

  useEffect(() => {
    if (status === 'unauthenticated') {
      setChecking(false)
      return
    }
    if (!token) {
      setChecking(false)
      return
    }
    let cancelled = false
    ;(async () => {
      try {
        const r = await fetch(`${base}/api/auth/me`, { headers: authHeaders(token), cache: 'no-store' })
        const d = await r.json().catch(() => ({}))
        if (cancelled) return
        if (r.ok && d.user?.birth_year != null) {
          await update({ birthYearComplete: true })
          router.replace(callbackUrl.startsWith('/') ? callbackUrl : '/chat')
          return
        }
      } catch {
        /* ignore */
      } finally {
        if (!cancelled) setChecking(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [status, token, base, callbackUrl, router, update])

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    const y = parseInt(year, 10)
    const nowY = new Date().getFullYear()
    if (!Number.isFinite(y) || y < 1900 || y > nowY) {
      setError(`Enter a valid year between 1900 and ${nowY}.`)
      return
    }
    if (!token) {
      setError('Session expired. Please sign in again.')
      return
    }
    setSaving(true)
    try {
      const r = await fetch(`${base}/api/auth/me`, {
        method: 'PATCH',
        headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
        body: JSON.stringify({ birth_year: y }),
      })
      const d = await r.json().catch(() => ({}))
      if (!r.ok) {
        setError(d.error || 'Could not save. Try again.')
        return
      }
      await update({ birthYearComplete: true })
      router.replace(callbackUrl.startsWith('/') ? callbackUrl : '/chat')
      router.refresh()
    } catch {
      setError('Network error. Check your connection.')
    } finally {
      setSaving(false)
    }
  }

  if (status === 'loading' || checking) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <p>Loading…</p>
        </div>
      </div>
    )
  }

  if (status === 'unauthenticated') {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <p>Please sign in first.</p>
          <Link href={`/login?callbackUrl=/onboarding`}>Sign in</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Year of birth</h1>
        <p className="auth-sub">
          We use this only to tailor response style (child, teen, or adult). You can change it anytime in Settings.
        </p>
        <form className="auth-form" onSubmit={onSubmit}>
          {error && <p className="auth-error">{error}</p>}
          <label>
            Year you were born
            <input
              type="number"
              inputMode="numeric"
              min={1900}
              max={new Date().getFullYear()}
              value={year}
              onChange={(e) => setYear(e.target.value)}
              required
              autoComplete="bday-year"
              placeholder="e.g. 1995"
            />
          </label>
          <button type="submit" className="auth-submit" disabled={saving}>
            {saving ? 'Saving…' : 'Continue'}
          </button>
        </form>
        <p className="auth-footer">
          <Link href="/settings">Settings</Link>
          {' · '}
          <Link href="/">Home</Link>
        </p>
      </div>
    </div>
  )
}

export default function OnboardingPage() {
  return (
    <Suspense fallback={<div className="auth-page">Loading…</div>}>
      <OnboardingForm />
    </Suspense>
  )
}
