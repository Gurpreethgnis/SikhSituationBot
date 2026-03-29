'use client'

import React, { useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import { apiBase, authHeaders } from '../../lib/api'
import Link from 'next/link'

export default function AdminHomePage() {
  const { data: session } = useSession()
  const token = session?.accessToken
  const [stats, setStats] = useState(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    if (!token) return
    let cancelled = false
    ;(async () => {
      try {
        const r = await fetch(`${apiBase()}/api/admin/analytics`, { headers: authHeaders(token) })
        const d = await r.json()
        if (!r.ok) throw new Error(d.error || r.statusText)
        if (!cancelled) setStats(d)
      } catch (e) {
        if (!cancelled) setErr(e.message || 'Failed to load')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [token])

  return (
    <div>
      <h1 className="admin-page-title">Overview</h1>
      {err && <p className="admin-error">{err}</p>}
      {stats && (
        <div className="admin-cards">
          <div className="admin-card">
            <strong>{stats.users}</strong>
            <span>Users</span>
          </div>
          <div className="admin-card">
            <strong>{stats.chats}</strong>
            <span>Chats</span>
          </div>
          <div className="admin-card">
            <strong>{stats.messages}</strong>
            <span>Messages</span>
          </div>
          <div className="admin-card">
            <strong>{stats.shabads}</strong>
            <span>Shabads</span>
          </div>
        </div>
      )}
      <p>
        <Link href="/admin/users">Manage users</Link>
        {' · '}
        <Link href="/admin/shabads">Manage Shabads</Link>
        {' · '}
        <Link href="/admin/analytics">Analytics detail</Link>
        {' · '}
        <Link href="/admin/interactions">Interactions log</Link>
        {' · '}
        <Link href="/admin/llm">LLM settings</Link>
      </p>
    </div>
  )
}
