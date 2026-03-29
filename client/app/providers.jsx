'use client'

import { SessionProvider } from 'next-auth/react'
import { ThemeProvider } from './contexts/ThemeContext'

export function Providers({ children }) {
  return (
    <SessionProvider refetchInterval={5 * 60}>
      <ThemeProvider>{children}</ThemeProvider>
    </SessionProvider>
  )
}
