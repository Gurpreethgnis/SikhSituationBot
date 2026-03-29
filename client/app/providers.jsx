'use client'

import { SessionProvider } from 'next-auth/react'
import { ThemeProvider } from './contexts/ThemeContext'
import { TranslationProvider } from './contexts/TranslationContext'

export function Providers({ children }) {
  return (
    <SessionProvider refetchInterval={5 * 60}>
      <ThemeProvider>
        <TranslationProvider>{children}</TranslationProvider>
      </ThemeProvider>
    </SessionProvider>
  )
}
