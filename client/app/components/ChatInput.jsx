'use client'

import { useState, useRef } from 'react'
import './ChatInput.css'

/**
 * Chat composer styled like ChatGPT: single rounded bar, optional left control (+ menu), send on the right.
 */
export default function ChatInput({ onSend, placeholder, disabled, loading, startAdornment }) {
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
    <form className="chat-input chat-input--gpt" onSubmit={handleSubmit}>
      <div className="chat-input__shell">
        {startAdornment}
        <input
          ref={inputRef}
          type="text"
          className="chat-input__field"
          placeholder={placeholder ?? 'Message SikhSituationBot…'}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          aria-label="Message"
          autoComplete="off"
        />
        <button
          type="submit"
          className="chat-input__send"
          disabled={!value.trim() || disabled || loading}
          aria-label="Send message"
        >
          {loading ? (
            <span className="chat-input__spinner" aria-hidden />
          ) : (
            <svg className="chat-input__send-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
              <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.167.75.75 0 0 0 0-1.666A60.517 60.517 0 0 0 3.478 2.404Z" />
            </svg>
          )}
        </button>
      </div>
    </form>
  )
}
