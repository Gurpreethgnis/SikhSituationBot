'use client'

import React, { useState } from 'react'
import './SharedMessageCopy.css'

export default function SharedMessageCopy({ content, copyLabel, copiedLabel }) {
  const [done, setDone] = useState(false)

  async function onCopy() {
    try {
      await navigator.clipboard.writeText(content || '')
      setDone(true)
      setTimeout(() => setDone(false), 2000)
    } catch {
      /* ignore */
    }
  }

  return (
    <button type="button" className="shared-copy-btn" onClick={onCopy} aria-label={copyLabel}>
      {done ? copiedLabel : copyLabel}
    </button>
  )
}
