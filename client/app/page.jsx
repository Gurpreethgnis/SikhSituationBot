import Link from 'next/link'
import './landing.css'

export default function LandingPage() {
  return (
    <div className="landing">
      <div className="landing-inner">
        <div className="landing-logo" aria-hidden>
          ☬
        </div>
        <h1>SikhSituationBot</h1>
        <p className="landing-tagline">
          Seek perspective from Guru Granth Sahib for life&apos;s situations — with respectful, age-aware
          guidance and semantic discovery of Gurbani.
        </p>
        <div className="landing-actions">
          <Link href="/chat" className="landing-btn landing-btn-primary">
            Open app
          </Link>
          <Link href="/login" className="landing-btn landing-btn-secondary">
            Sign in
          </Link>
          <Link href="/register" className="landing-btn landing-btn-ghost">
            Create account
          </Link>
        </div>
        <p className="landing-foot">
          <Link href="/parmaans">Browse Parmaans &amp; Shabads</Link>
          {' · '}
          <span>Spiritual perspective only — not professional advice.</span>
        </p>
      </div>
    </div>
  )
}
