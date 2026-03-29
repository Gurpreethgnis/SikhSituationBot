'use client'

import React, { useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import { apiBase, authHeaders } from '../../../lib/api'

export default function AdminAnalyticsPage() {
  const { data: session } = useSession()
  const token = session?.accessToken
  const [data, setData] = useState(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    if (!token) return
    ;(async () => {
      try {
        const r = await fetch(`${apiBase()}/api/admin/analytics`, { headers: authHeaders(token) })
        const d = await r.json()
        if (!r.ok) throw new Error(d.error || r.statusText)
        setData(d)
      } catch (e) {
        setErr(e.message || 'Failed')
      }
    })()
  }, [token])

  return (
    <div>
      <h1 className="admin-page-title">Analytics</h1>
      {err && <p className="admin-error">{err}</p>}
      {data && (
        <>
          <div className="admin-cards">
            <div className="admin-card">
              <strong>{data.users}</strong>
              <span>Registered users</span>
            </div>
            <div className="admin-card">
              <strong>{data.chats}</strong>
              <span>Chats</span>
            </div>
            <div className="admin-card">
              <strong>{data.messages}</strong>
              <span>Messages stored</span>
            </div>
            <div className="admin-card">
              <strong>{data.shabads}</strong>
              <span>Shabads in index</span>
            </div>
          </div>
          <section>
            <h2 style={{ fontSize: '1rem' }}>Response languages (API)</h2>
            <ul>
              {(data.languages_supported || []).map((l) => (
                <li key={l}>{l}</li>
              ))}
            </ul>
            <p style={{ color: 'var(--color-text-secondary, #b8b8d1)', fontSize: '0.85rem' }}>
              For deeper charts (DAU, topics), wire a metrics pipeline or export logs — this dashboard shows
              datastore counts only.
            </p>
          </section>
        </>
      )}
    </div>
  )
}
