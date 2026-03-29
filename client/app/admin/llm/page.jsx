'use client'

import React, { useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import { apiBase, authHeaders } from '../../../lib/api'
import '../admin.css'

export default function AdminLLMPage() {
  const { data: session } = useSession()
  const token = session?.accessToken
  const [options, setOptions] = useState(null)
  const [provider, setProvider] = useState('gemini')
  const [modelId, setModelId] = useState('')
  const [err, setErr] = useState('')
  const [msg, setMsg] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!token) return
    let c = false
    ;(async () => {
      try {
        const r = await fetch(`${apiBase()}/api/admin/llm-settings`, { headers: authHeaders(token) })
        const d = await r.json()
        if (!r.ok) throw new Error(d.error || r.statusText)
        if (c) return
        setOptions(d.options)
        setProvider(d.provider)
        setModelId(d.model_id)
      } catch (e) {
        if (!c) setErr(e.message || 'Failed to load')
      }
    })()
    return () => {
      c = true
    }
  }, [token])

  const modelsForProvider = options?.models_by_provider?.[provider] || []

  const onProviderChange = (p) => {
    setProvider(p)
    const list = options?.models_by_provider?.[p] || []
    if (list.length) setModelId(list[0])
  }

  const save = async (e) => {
    e.preventDefault()
    if (!token) return
    setSaving(true)
    setErr('')
    setMsg('')
    try {
      const r = await fetch(`${apiBase()}/api/admin/llm-settings`, {
        method: 'PATCH',
        headers: authHeaders(token),
        body: JSON.stringify({ provider, model_id: modelId }),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.error || r.statusText)
      setMsg(`Saved: ${d.provider} / ${d.model_id}`)
    } catch (e2) {
      setErr(e2.message || 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <h1 className="admin-page-title">LLM provider</h1>
      <p className="admin-muted">
        Chooses which API answers /ask (after retrieval). Set the matching API key in the server environment
        (GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY).
      </p>

      {!options && !err && <p className="admin-muted">Loading…</p>}
      {err && <p className="admin-error">{err}</p>}

      {options && (
        <form className="admin-form" onSubmit={save} style={{ maxWidth: 480 }}>
          <label>
            Provider
            <select value={provider} onChange={(e) => onProviderChange(e.target.value)}>
              {(options.providers || []).map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </label>
          <label>
            Model
            <select value={modelId} onChange={(e) => setModelId(e.target.value)}>
              {modelsForProvider.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </label>
          {msg && <p className="admin-success">{msg}</p>}
          <button type="submit" className="admin-btn-primary" disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
        </form>
      )}
    </div>
  )
}
