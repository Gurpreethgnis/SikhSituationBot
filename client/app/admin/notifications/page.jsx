'use client'

import React, { useState } from 'react'
import { useSession } from 'next-auth/react'
import { apiBase, authHeaders } from '../../../lib/api'
import Link from 'next/link'

export default function AdminPushPage() {
  const { data: session } = useSession()
  const token = session?.accessToken
  const [title, setTitle] = useState('Giani Ji')
  const [body, setBody] = useState('')
  const [email, setEmail] = useState('')
  const [sending, setSending] = useState(false)
  const [msg, setMsg] = useState('')

  const sendAll = async () => {
    if (!confirm('Send to ALL users with registered devices?')) return
    setSending(true)
    setMsg('')
    try {
      const r = await fetch(`${apiBase()}/api/admin/push-all`, {
        method: 'POST',
        headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, body }),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.error || 'Failed')
      setMsg(`Success! Sent to ${d.sent} users.`)
    } catch (e) {
      setMsg(`Error: ${e.message}`)
    } finally {
      setSending(false)
    }
  }

  const sendSingle = async () => {
    if (!email) return
    setSending(true)
    setMsg('')
    try {
      const r = await fetch(`${apiBase()}/api/admin/push-single`, {
        method: 'POST',
        headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, body, email }),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.error || 'Failed')
      setMsg(`Success! Notification sent to ${email}.`)
    } catch (e) {
      setMsg(`Error: ${e.message}`)
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="admin-push-container">
      <Link href="/admin" className="admin-back-link">← Back to Overview</Link>
      <h1 className="admin-page-title">Push Notifications</h1>
      <p className="admin-hint">Send manual notifications to mobile app users via Expo.</p>
      
      <div className="admin-form-section">
        <label>Notification Title</label>
        <input 
          type="text" 
          value={title} 
          onChange={(e) => setTitle(e.target.value)} 
          placeholder="Giani Ji"
        />

        <label>Message Body</label>
        <textarea 
          value={body} 
          onChange={(e) => setBody(e.target.value)} 
          placeholder="Share your situation with Giani Ji..."
          rows={3}
        />

        <div className="admin-actions">
          <button 
            className="admin-btn admin-btn-primary" 
            onClick={sendAll} 
            disabled={sending || !body}
          >
            {sending ? 'Sending...' : 'Push to ALL Users'}
          </button>
        </div>
      </div>

      <div className="admin-form-section" style={{ marginTop: '40px' }}>
        <h3>Send to Specific User</h3>
        <label>User Email</label>
        <div style={{ display: 'flex', gap: '10px' }}>
          <input 
            type="email" 
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
            placeholder="user@example.com"
          />
          <button 
            className="admin-btn" 
            onClick={sendSingle} 
            disabled={sending || !body || !email}
          >
            {sending ? '...' : 'Send'}
          </button>
        </div>
      </div>

      {msg && <p className="admin-status-msg">{msg}</p>}

      <style jsx>{`
        .admin-push-container { max-width: 600px; }
        .admin-form-section { background: var(--color-bg-elevated); border: 1px solid var(--color-border); border-radius: 12px; padding: 24px; margin-top: 20px; }
        label { display: block; font-size: 13px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 8px; }
        input, textarea { width: 100%; background: var(--color-bg-elevated); border: 1px solid var(--color-border); border-radius: 8px; color: var(--text-primary); padding: 12px; margin-bottom: 20px; font-family: inherit; }
        .admin-actions { display: flex; gap: 10px; }
        .admin-status-msg { margin-top: 20px; font-weight: 600; color: var(--color-accent); }
        .admin-back-link { display: block; margin-bottom: 10px; color: var(--text-secondary); font-size: 14px; text-decoration: none; }
        h3 { color: var(--text-primary); margin-top: 0; }
      `}</style>
    </div>
  )
}
