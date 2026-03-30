'use client'

import { signIn, getProviders } from 'next-auth/react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState, useEffect } from 'react'
import { apiBase } from '../../lib/api'
import '../auth.css'

const CONFIG_ERROR_HINT =
  'NextAuth is misconfigured: set NEXTAUTH_SECRET (and NEXTAUTH_URL) in your deployment env. On Vercel: Project → Settings → Environment Variables. Generate a secret: openssl rand -base64 32'

export default function RegisterPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showGoogle, setShowGoogle] = useState(false)

  useEffect(() => {
    getProviders().then((p) => setShowGoogle(Boolean(p?.google)))
  }, [])

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await fetch(`${apiBase()}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name: name || undefined }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        setError(data.error || 'Registration failed')
        setLoading(false)
        return
      }
      const sign = await signIn('credentials', {
        email,
        password,
        redirect: false,
        callbackUrl: '/chat',
      })
      if (sign?.error) {
        if (sign.error === 'Configuration') {
          setError(
            `Account was created on the server, but session sign-in failed: ${CONFIG_ERROR_HINT}`
          )
        } else {
          setError('Account created but sign-in failed. Try logging in.')
        }
        setLoading(false)
        return
      }
      router.push('/chat')
      router.refresh()
    } catch {
      const base = apiBase()
      setError(
        base
          ? `Cannot reach the API at ${base}. Check NEXT_PUBLIC_API_URL and CORS.`
          : 'Cannot reach the API (same-origin proxy). Set FLASK_API_URL on the Next.js host at build time, or set NEXT_PUBLIC_API_URL to your Flask URL.',
      )
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Create account</h1>
        <p className="auth-sub">Save conversations, share chats, and sync preferences.</p>

        {showGoogle && (
          <>
            <button
              type="button"
              className="auth-google"
              onClick={() => signIn('google', { callbackUrl: '/chat' })}
              disabled={loading}
            >
              Continue with Google
            </button>
            <div className="auth-divider">or register with email</div>
          </>
        )}

        <form onSubmit={onSubmit} className="auth-form">
          {error && <p className="auth-error">{error}</p>}
          <label>
            Name (optional)
            <input value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" />
          </label>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </label>
          <label>
            Password (8+ characters)
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
            />
          </label>
          <button type="submit" className="auth-submit" disabled={loading}>
            {loading ? 'Creating…' : 'Register'}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account? <Link href="/login">Sign in</Link>
          {' · '}
          <Link href="/">Home</Link>
        </p>
      </div>
    </div>
  )
}
