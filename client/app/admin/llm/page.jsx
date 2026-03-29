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
  const [guidanceShabadCount, setGuidanceShabadCount] = useState(3)
  const [parmaanShabadCount, setParmaanShabadCount] = useState(5)
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
        setGuidanceShabadCount(d.guidance_shabad_count || 3)
        setParmaanShabadCount(d.parmaan_shabad_count || 5)
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
        body: JSON.stringify({
          provider,
          model_id: modelId,
          guidance_shabad_count: guidanceShabadCount,
          parmaan_shabad_count: parmaanShabadCount,
        }),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.error || r.statusText)
      setMsg(`Settings saved successfully`)
    } catch (e2) {
      setErr(e2.message || 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <h1 className="admin-page-title">LLM Settings</h1>
      <p className="admin-muted">
        Configure the AI provider, model, and shabad retrieval settings.
      </p>

      {!options && !err && <p className="admin-muted">Loading…</p>}
      {err && <p className="admin-error">{err}</p>}

      {options && (
        <form className="admin-form" onSubmit={save} style={{ maxWidth: 520 }}>
          <fieldset style={{ marginBottom: '1.5rem', padding: '1rem', border: '1px solid var(--color-border)', borderRadius: '8px' }}>
            <legend style={{ fontWeight: 600, padding: '0 0.5rem' }}>AI Provider</legend>
            <p className="admin-muted" style={{ fontSize: '0.85rem', marginBottom: '1rem' }}>
              Set the matching API key in the server environment (GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY).
            </p>
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
          </fieldset>

          <fieldset style={{ marginBottom: '1.5rem', padding: '1rem', border: '1px solid var(--color-border)', borderRadius: '8px' }}>
            <legend style={{ fontWeight: 600, padding: '0 0.5rem' }}>Shabad Retrieval</legend>
            <p className="admin-muted" style={{ fontSize: '0.85rem', marginBottom: '1rem' }}>
              Configure how many shabads are retrieved for each mode.
            </p>
            <label>
              Guidance Mode - Number of Shabads (1-10)
              <input
                type="number"
                min="1"
                max="10"
                value={guidanceShabadCount}
                onChange={(e) => setGuidanceShabadCount(parseInt(e.target.value) || 3)}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--color-border)' }}
              />
              <span className="admin-muted" style={{ fontSize: '0.8rem', display: 'block', marginTop: '0.25rem' }}>
                Shabads retrieved when users describe life situations for guidance.
              </span>
            </label>
            <label style={{ marginTop: '1rem' }}>
              Parmaan Mode - Number of Shabads (1-15)
              <input
                type="number"
                min="1"
                max="15"
                value={parmaanShabadCount}
                onChange={(e) => setParmaanShabadCount(parseInt(e.target.value) || 5)}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--color-border)' }}
              />
              <span className="admin-muted" style={{ fontSize: '0.8rem', display: 'block', marginTop: '0.25rem' }}>
                Shabads returned when users search for shabads on a topic.
              </span>
            </label>
          </fieldset>

          {msg && <p className="admin-success">{msg}</p>}
          <button type="submit" className="admin-btn-primary" disabled={saving}>
            {saving ? 'Saving…' : 'Save Settings'}
          </button>
        </form>
      )}
    </div>
  )
}
