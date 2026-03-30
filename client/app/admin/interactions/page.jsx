'use client'

import React, { useCallback, useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import { apiBase, authHeaders } from '../../../lib/api'
import '../admin.css'

export default function AdminInteractionsPage() {
  const { data: session } = useSession()
  const token = session?.accessToken
  const [page, setPage] = useState(1)
  const [full, setFull] = useState(false)
  const [filterEmail, setFilterEmail] = useState('')
  const [searchKey, setSearchKey] = useState(0)
  const [data, setData] = useState(null)
  const [err, setErr] = useState('')

  const load = useCallback(async () => {
    if (!token) return
    setErr('')
    try {
      const q = new URLSearchParams({
        page: String(page),
        per_page: '40',
        full: full ? 'true' : 'false',
      })
      if (filterEmail.trim()) q.set('user_email', filterEmail.trim())
      const r = await fetch(`${apiBase()}/api/admin/interactions?${q}`, { headers: authHeaders(token) })
      const d = await r.json()
      if (!r.ok) throw new Error(d.error || r.statusText)
      setData(d)
    } catch (e) {
      setErr(e.message || 'Failed to load')
      setData(null)
    }
  }, [token, page, full, filterEmail])

  useEffect(() => {
    load()
  }, [load, searchKey])

  return (
    <div>
      <h1 className="admin-page-title">Interactions</h1>
      <p className="admin-muted">
        Messages across all chats: questions, assistant replies, persona, language, linked Parmaan, and LLM metadata.
      </p>

      <div className="admin-toolbar">
        <label className="admin-field">
          <span>User email contains</span>
          <input
            type="search"
            value={filterEmail}
            onChange={(e) => setFilterEmail(e.target.value)}
            placeholder="optional"
          />
        </label>
        <label className="admin-check">
          <input type="checkbox" checked={full} onChange={(e) => setFull(e.target.checked)} />
          Full message text
        </label>
        <button
          type="button"
          className="admin-btn"
          onClick={() => {
            setPage(1)
            setSearchKey((k) => k + 1)
          }}
        >
          Apply
        </button>
      </div>

      {err && <p className="admin-error">{err}</p>}

      {data && (
        <>
          <p className="admin-muted">
            Total {data.total} · page {data.page} of {Math.max(1, Math.ceil(data.total / data.per_page))}
          </p>
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>When</th>
                  <th>User</th>
                  <th>Chat</th>
                  <th>Role</th>
                  <th>Lang</th>
                  <th>LLM</th>
                  <th>Content</th>
                </tr>
              </thead>
              <tbody>
                {(data.items || []).map((row) => (
                  <tr key={row.message_id}>
                    <td className="admin-nowrap">{row.created_at?.replace('T', ' ').slice(0, 19)}</td>
                    <td>{row.user_email}</td>
                    <td title={row.chat_title}>
                      #{row.chat_id}
                      {row.chat_title ? ` · ${row.chat_title.slice(0, 24)}` : ''}
                    </td>
                    <td>{row.role}</td>
                    <td>{row.language}</td>
                    <td className="admin-llm-cell">
                      {row.llm_provider || '—'}
                      {row.llm_model ? <small>{row.llm_model}</small> : null}
                    </td>
                    <td className="admin-content-cell">
                      <div className="admin-content-preview">{row.content}</div>
                      {row.shabad && (
                        <div className="admin-shabad-ref">
                          Shabad {row.shabad.shabad_id}: {row.shabad.english_translation}
                        </div>
                      )}
                      {row.content_truncated && !full && (
                        <span className="admin-muted">(truncated — enable full text)</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="admin-pagination">
            <button
              type="button"
              className="admin-btn"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </button>
            <button
              type="button"
              className="admin-btn"
              disabled={!data || page * data.per_page >= data.total}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  )
}
