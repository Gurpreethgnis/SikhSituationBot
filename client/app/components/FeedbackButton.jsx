'use client'

import React from 'react'

/**
 * Opens feedback modal for the given assistant message (toolbar control).
 */
export default function FeedbackButton({ onClick, label, disabled }) {
  return (
    <button
      type="button"
      className="feedback-btn"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={label}
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
        <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
        <line x1="4" y1="22" x2="4" y2="15" />
      </svg>
      <span className="feedback-btn__text">{label}</span>
    </button>
  )
}
