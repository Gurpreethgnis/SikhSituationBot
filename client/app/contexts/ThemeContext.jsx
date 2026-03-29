'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'

export const THEMES = [
  { id: 'basanti', name: 'Basanti', description: 'Traditional yellow' },
  { id: 'neela', name: 'Neela', description: 'Traditional blue' },
  { id: 'light', name: 'Light', description: 'High contrast' },
  { id: 'khalsa-gold', name: 'Khalsa Gold', description: 'Warm gold' },
  { id: 'nihangs-navy', name: 'Nihangs Navy', description: 'Deep navy' },
]

const DEFAULT_THEME = 'basanti'
const ThemeContext = createContext(null)

const STORAGE_KEY = 'sikh_bot_theme'

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(DEFAULT_THEME)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved && THEMES.some((t) => t.id === saved)) {
        setThemeState(saved)
        document.documentElement.setAttribute('data-theme', saved)
      } else {
        document.documentElement.setAttribute('data-theme', DEFAULT_THEME)
      }
    } catch {
      document.documentElement.setAttribute('data-theme', DEFAULT_THEME)
    }
    setReady(true)
  }, [])

  useEffect(() => {
    if (!ready) return
    document.documentElement.setAttribute('data-theme', theme)
    try {
      localStorage.setItem(STORAGE_KEY, theme)
    } catch {
      /* ignore */
    }
  }, [theme, ready])

  const setTheme = (id) => {
    if (THEMES.some((t) => t.id === id)) {
      setThemeState(id)
      document.documentElement.setAttribute('data-theme', id)
    }
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, themes: THEMES, ready }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
