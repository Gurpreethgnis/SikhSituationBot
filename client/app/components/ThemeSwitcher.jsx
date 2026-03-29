'use client'

import React from 'react'
import { useTheme } from '../contexts/ThemeContext'
import './ThemeSwitcher.css'

export default function ThemeSwitcher({ compact = false }) {
  const { theme, setTheme, themes } = useTheme()

  if (compact) {
    return (
      <select
        className="theme-switcher-select"
        value={theme}
        onChange={(e) => setTheme(e.target.value)}
        aria-label="Theme"
      >
        {themes.map((t) => (
          <option key={t.id} value={t.id}>
            {t.name}
          </option>
        ))}
      </select>
    )
  }

  return (
    <div className="theme-switcher">
      <span className="theme-switcher-label">Theme</span>
      <div className="theme-switcher-grid">
        {themes.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`theme-switcher-btn ${theme === t.id ? 'active' : ''}`}
            data-theme-preview={t.id}
            title={t.description}
            onClick={() => setTheme(t.id)}
          >
            {t.name}
          </button>
        ))}
      </div>
    </div>
  )
}
