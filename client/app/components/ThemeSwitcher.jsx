'use client'

import React from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { useTranslation } from '../contexts/TranslationContext.jsx'
import './ThemeSwitcher.css'

export default function ThemeSwitcher({ compact = false }) {
  const { theme, setTheme, themes } = useTheme()
  const { t } = useTranslation()

  if (compact) {
    return (
      <select
        className="theme-switcher-select"
        value={theme}
        onChange={(e) => setTheme(e.target.value)}
        aria-label={t('theme')}
      >
        {themes.map((th) => (
          <option key={th.id} value={th.id}>
            {th.name}
          </option>
        ))}
      </select>
    )
  }

  return (
    <div className="theme-switcher">
      <span className="theme-switcher-label">{t('theme')}</span>
      <div className="theme-switcher-grid">
        {themes.map((th) => (
          <button
            key={th.id}
            type="button"
            className={`theme-switcher-btn ${theme === th.id ? 'active' : ''}`}
            data-theme-preview={th.id}
            title={th.description}
            onClick={() => setTheme(th.id)}
          >
            {th.name}
          </button>
        ))}
      </div>
    </div>
  )
}
