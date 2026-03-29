import Link from 'next/link'
import Logo from './components/Logo'
import './landing.css'

export default function LandingPage() {
  return (
    <div className="landing">
      <div className="landing-inner">
        <div className="landing-brand">
          <Logo />
        </div>
        <h1>SikhSituationBot</h1>
        <p className="landing-tagline">
          Seek perspective from Guru Granth Sahib for life&apos;s situations — with respectful, age-aware
          guidance and semantic discovery of Gurbani.
        </p>
        <div className="landing-actions">
          <Link href="/login?callbackUrl=/chat" className="landing-btn landing-btn-primary">
            Sign in to chat
          </Link>
          <Link href="/register" className="landing-btn landing-btn-secondary">
            Create account
          </Link>
          <Link href="/login?callbackUrl=/parmaans" className="landing-btn landing-btn-ghost">
            Sign in to browse Parmaans
          </Link>
        </div>
        <p className="landing-foot">
          Chat and Parmaans require an account —{' '}
          <Link href="/login?callbackUrl=/chat">Sign in</Link>
          {' · '}
          <span>Spiritual perspective only — not professional advice.</span>
        </p>
      </div>
    </div>
  )
}
