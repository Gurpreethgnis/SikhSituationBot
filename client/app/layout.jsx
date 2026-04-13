import './globals.css'
import './styles/themes.css'
import { Providers } from './providers'

export const metadata = {
  title: 'Giani Ji',
  description: "Gurbani-based guidance for life's moments",
}

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning data-theme="basanti">
      <body suppressHydrationWarning>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
