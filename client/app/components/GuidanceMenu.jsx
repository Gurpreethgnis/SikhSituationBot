'use client'

import React, { useEffect, useRef, useState } from 'react'
import './GuidanceMenu.css'

const MODES = [
  {
    id: 'parmaan',
    label: 'Parmaan-grounded',
    hint: 'Retrieve a relevant shabad and reflect on it.',
  },
  {
    id: 'situational',
    label: 'Situational advice',
    hint: 'General Sikhi-aligned perspective without a retrieved verse.',
  },
]

export default function GuidanceMenu({ mode, onModeChange, disabled, variant }) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef(null)

  useEffect(() => {
    if (!open) return
    const onDoc = (e) => {
      if (rootRef.current && !rootRef.current.contains(e.target)) setOpen(false)
    }
    const onKey = (e) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDoc)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  const active = MODES.find((m) => m.id === mode) || MODES[0]

  return (
    <div className={`guidance-menu${variant === 'embed' ? ' guidance-menu--embed' : ''}`} ref={rootRef}>
      <button
        type="button"
        className="guidance-menu__trigger"
        aria-expanded={open}
        aria-haspopup="menu"
        aria-label="Choose guidance type"
        disabled={disabled}
        onClick={() => setOpen((o) => !o)}
      >
        <span className="guidance-menu__plus" aria-hidden>
          +
        </span>
      </button>
      {open && (
        <div className="guidance-menu__popover" role="menu" aria-label="Guidance type">
          {MODES.map((m) => (
            <button
              key={m.id}
              type="button"
              role="menuitemradio"
              aria-checked={mode === m.id}
              className={`guidance-menu__option ${mode === m.id ? 'guidance-menu__option--active' : ''}`}
              onClick={() => {
                onModeChange(m.id)
                setOpen(false)
              }}
            >
              <span className="guidance-menu__option-title">{m.label}</span>
              <span className="guidance-menu__option-hint">{m.hint}</span>
            </button>
          ))}
        </div>
      )}
      <span className="guidance-menu__current-label sr-only">{active.label}</span>
    </div>
  )
}
