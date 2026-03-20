import './globals.css'

export const metadata = {
  title: 'SikhSituationBot',
  description: 'Gurbani-based guidance for life\'s moments',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        {children}
      </body>
    </html>
  )
}
