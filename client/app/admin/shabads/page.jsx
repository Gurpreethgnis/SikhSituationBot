'use client'

import React, { useCallback, useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import { apiBase, authHeaders } from '../../../lib/api'

const emptyForm = {
  shabad_id: '',
  gurmukhi: '',
  english_translation: '',
  romanization: '',
  source: '',
  recommended_persona: 'any',
}

export default function AdminShabadsPage() {
  const { data: session } = useSession()
  const token = session?.accessToken
  const [shabads, setShabads] = useState([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [q, setQ] = useState('')
  const [form, setForm] = useState(emptyForm)
  const [err, setErr] = useState('')
  const [msg, setMsg] = useState('')

  const load = useCallback(async () => {
    if (!token) return
    setErr('')
    try {
      const params = new URLSearchParams({ page: String(page), per_page: '25' })
      if (q.trim()) params.set('q', q.trim())
      const r = await fetch(`${apiBase()}/api/admin/shabads?${params}`, { headers: authHeaders(token) })
      const d = await r.json()
      if (!r.ok) throw new Error(d.error || r.statusText)
      setShabads(d.shabads || [])
      setTotal(d.total || 0)
    } catch (e) {
      setErr(e.message || 'Failed')
    }
  }, [token, page, q])

  useEffect(() => {
    load()
  }, [load])

  const submitCreate = async (e) => {
    e.preventDefault()
    setMsg('')
    try {
      const r = await fetch(`${apiBase()}/api/admin/shabads`, {
        method: 'POST',
        headers: authHeaders(token),
        body: JSON.stringify(form),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.error || r.statusText)
      setForm(emptyForm)
      setMsg('Shabad created.')
      await load()
    } catch (e) {
      setErr(e.message || 'Create failed')
    }
  }

  const del = async (id) => {
    if (!confirm('Delete this Shabad?')) return
    try {
      const r = await fetch(`${apiBase()}/api/admin/shabads/${id}`, {
        method: 'DELETE',
        headers: authHeaders(token),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.error || r.statusText)
      await load()
    } catch (e) {
      alert(e.message)
    }
  }

  return (
    <div>
      <h1 className="admin-page-title">Shabads</h1>
      {err && <p className="admin-error">{err}</p>}
      {msg && <p className="admin-success">{msg}</p>}

      <form className="admin-form" onSubmit={submitCreate}>
        <h2 className="admin-section-title">Add Shabad</h2>
        <label>
          Shabad key (STTM id / unique)
          <input
            value={form.shabad_id}
            onChange={(e) => setForm((f) => ({ ...f, shabad_id: e.target.value }))}
            required
          />
        </label>
        <label>
          Gurmukhi
          <textarea
            value={form.gurmukhi}
            onChange={(e) => setForm((f) => ({ ...f, gurmukhi: e.target.value }))}
            required
          />
        </label>
        <label>
          English translation
          <textarea
            value={form.english_translation}
            onChange={(e) => setForm((f) => ({ ...f, english_translation: e.target.value }))}
            required
          />
        </label>
        <label>
          Romanization
          <input
            value={form.romanization}
            onChange={(e) => setForm((f) => ({ ...f, romanization: e.target.value }))}
          />
        </label>
        <label>
          Source
          <input value={form.source} onChange={(e) => setForm((f) => ({ ...f, source: e.target.value }))} />
        </label>
        <label>
          Persona
          <input
            value={form.recommended_persona}
            onChange={(e) => setForm((f) => ({ ...f, recommended_persona: e.target.value }))}
          />
        </label>
        <button type="submit" className="admin-btn-primary">
          Create &amp; embed
        </button>
      </form>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          setPage(1)
          load()
        }}
        className="admin-form admin-form--inline"
        style={{ maxWidth: '100%', flexDirection: 'row', alignItems: 'flex-end' }}
      >
        <label style={{ flex: 1 }}>
          Search
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Gurmukhi / English / source" />
        </label>
        <button type="submit" className="admin-btn">
          Search
        </button>
      </form>

      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Key</th>
              <th>English</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {shabads.map((s) => (
              <tr key={s.id}>
                <td>{s.id}</td>
                <td>{s.shabad_id}</td>
                <td>{s.english_translation?.slice(0, 80)}</td>
                <td>
                  <button type="button" onClick={() => del(s.id)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="admin-pagination-note">
        Page {page} — {total} total{' '}
        <button type="button" className="admin-btn" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          Prev
        </button>{' '}
        <button type="button" className="admin-btn" disabled={page * 25 >= total} onClick={() => setPage((p) => p + 1)}>
          Next
        </button>
      </p>
    </div>
  )
}
