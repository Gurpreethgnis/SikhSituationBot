import './globals.css'
import './styles/themes.css'
import { Providers } from './providers'

export const metadata = {
  title: 'SikhSituationBot',
  description: "Gurbani-based guidance for life's moments",
}

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning data-theme="saffron">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
