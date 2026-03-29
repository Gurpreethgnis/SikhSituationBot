'use client'

import React, { useCallback, useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import { apiBase, authHeaders } from '../../../lib/api'

export default function AdminUsersPage() {
  const { data: session } = useSession()
  const token = session?.accessToken
  const [users, setUsers] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [err, setErr] = useState('')

  const load = useCallback(async () => {
    if (!token) return
    setErr('')
    try {
      const r = await fetch(`${apiBase()}/api/admin/users?page=${page}&per_page=40`, {
        headers: authHeaders(token),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.error || r.statusText)
      setUsers(d.users || [])
      setTotal(d.total || 0)
    } catch (e) {
      setErr(e.message || 'Failed')
    }
  }, [token, page])

  useEffect(() => {
    load()
  }, [load])

  const patchUser = async (id, body) => {
    try {
      const r = await fetch(`${apiBase()}/api/admin/users/${id}`, {
        method: 'PATCH',
        headers: authHeaders(token),
        body: JSON.stringify(body),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.error || r.statusText)
      await load()
      return d
    } catch (e) {
      alert(e.message)
    }
  }

  const deleteUser = async (id) => {
    if (!confirm('Delete this user and related data?')) return
    try {
      const r = await fetch(`${apiBase()}/api/admin/users/${id}`, {
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
      <h1 className="admin-page-title">Users</h1>
      {err && <p className="admin-error">{err}</p>}
      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Email</th>
              <th>Name</th>
              <th>Admin</th>
              <th>Active</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.id}</td>
                <td>{u.email}</td>
                <td>{u.name || '—'}</td>
                <td>{u.is_admin ? 'yes' : 'no'}</td>
                <td>{u.is_active === false ? 'no' : 'yes'}</td>
                <td>
                  <button type="button" onClick={() => patchUser(u.id, { is_admin: !u.is_admin })}>
                    Toggle admin
                  </button>
                  <button type="button" onClick={() => patchUser(u.id, { is_active: u.is_active === false })}>
                    Toggle active
                  </button>
                  <button type="button" onClick={() => deleteUser(u.id)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p>
        Page {page} — {total} total{' '}
        <button type="button" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          Prev
        </button>{' '}
        <button type="button" disabled={page * 40 >= total} onClick={() => setPage((p) => p + 1)}>
          Next
        </button>
      </p>
    </div>
  )
}
