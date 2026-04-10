import Link from 'next/link'
import MarkdownRenderer from '../../components/MarkdownRenderer'
import SharedMessageCopy from '../SharedMessageCopy.jsx'
import '../../landing.css'
import './shared.css'

export const dynamic = 'force-dynamic'

async function fetchShared(shareId) {
  const base = process.env.FLASK_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'
  const r = await fetch(`${base}/api/shared/${shareId}`, { next: { revalidate: 60 } })
  if (!r.ok) return null
  return r.json()
}

export async function generateMetadata({ params }) {
  const { shareId } = await params
  const data = await fetchShared(shareId)
  const title = data?.chat?.title || 'Shared conversation'
  return {
    title: `${title} · Giani Ji`,
    openGraph: {
      title,
      description: 'A shared spiritual perspective conversation from Giani Ji.',
    },
  }
}

export default async function SharedChatPage({ params }) {
  const { shareId } = await params
  const data = await fetchShared(shareId)
  if (!data?.chat) {
    return (
      <div className="shared-page">
        <p>This shared conversation was not found or is no longer public.</p>
        <Link href="/login?callbackUrl=/chat">Sign in to start your own conversation</Link>
      </div>
    )
  }

  const { title, messages } = data.chat

  return (
    <div className="shared-page">
      <header className="shared-header">
        <h1>{title || 'Shared conversation'}</h1>
        <p className="shared-sub">Read-only shared view. Spiritual perspective only — not professional advice.</p>
        <div className="shared-actions">
          <Link href="/login?callbackUrl=/chat" className="shared-cta">
            Sign in to start your own conversation
          </Link>
          <Link href="/" className="shared-link">
            Home
          </Link>
        </div>
      </header>
      <div className="shared-thread">
        {(messages || []).map((m, i) => (
          <article key={m.id || i} className={`shared-msg shared-msg--${m.role}`}>
            <div className="shared-msg-label">{m.role === 'user' ? 'You' : 'Guru'}</div>
            <div className="shared-msg-body">
              <MarkdownRenderer content={m.content || ''} />
              <SharedMessageCopy
                content={m.content || ''}
                copyLabel="Copy message"
                copiedLabel="Copied"
              />
              {m.shabad?.sttm_link &&
              typeof m.content === 'string' &&
              !m.content.includes('## Retrieved Gurbani') ? (
                <a className="shared-sttm" href={m.shabad.sttm_link} target="_blank" rel="noopener noreferrer">
                  View on SikhiToTheMax ↗
                </a>
              ) : null}
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}
