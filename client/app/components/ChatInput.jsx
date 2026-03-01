'use client'

import { useState, useRef } from 'react'
import './ChatInput.css'

/**
 * Premium chat input / search bar for SikhSituationBot.
 * Supports Enter to submit, optional send button, and clear loading/disabled states.
 */
export default function ChatInput({ onSend, placeholder, disabled, loading }) {
  const [value, setValue] = useState('')
  const inputRef = useRef(null)

  const handleSubmit = (e) => {
    e?.preventDefault()
    const trimmed = value.trim()
    if (!trimmed || disabled || loading) return
    onSend?.(trimmed)
    setValue('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      <div className="chat-input__wrapper">
        <input
          ref={inputRef}
          type="text"
          className="chat-input__field"
          placeholder={placeholder ?? 'Share how you\'re feeling or ask for guidance...'}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          aria-label="Chat message or search"
          autoComplete="off"
        />
        <button
          type="submit"
          className="chat-input__submit"
          disabled={!value.trim() || disabled || loading}
          aria-label="Send"
        >
          {loading ? (
            <span className="chat-input__spinner" aria-hidden />
          ) : (
            <svg className="chat-input__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
            </svg>
          )}
        </button>
      </div>
    </form>
  )
}
