'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'

export const THEMES = [
  { id: 'saffron', name: 'Saffron', description: 'Warm default' },
  { id: 'royal-blue', name: 'Royal Blue', description: 'Traditional blues' },
  { id: 'light', name: 'Light', description: 'High contrast' },
  { id: 'khalsa-gold', name: 'Khalsa Gold', description: 'Warm gold' },
  { id: 'nihangs-navy', name: 'Nihangs Navy', description: 'Deep navy' },
]

const ThemeContext = createContext(null)

const STORAGE_KEY = 'sikh_bot_theme'

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState('saffron')
  const [ready, setReady] = useState(false)

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved && THEMES.some((t) => t.id === saved)) {
        setThemeState(saved)
      }
    } catch {
      /* ignore */
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
    if (THEMES.some((t) => t.id === id)) setThemeState(id)
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, themes: THEMES }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
