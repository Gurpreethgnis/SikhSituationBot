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
        <h1>Giani Ji</h1>
        <p className="landing-tagline">
          Seek perspective from Guru Granth Sahib for life&apos;s situations — with respectful, age-aware
          guidance and semantic discovery of Gurbani.
        </p>
        <div className="landing-actions">
          <Link href="/login?callbackUrl=/chat" className="landing-btn landing-btn-primary">
            Sign in!
          </Link>
          <Link href="/register" className="landing-btn landing-btn-secondary">
            Create account
          </Link>
        </div>
        <p className="landing-foot">
          Chat and Parmaans use your account after you sign in. Spiritual perspective only — not professional advice.
        </p>
      </div>
    </div>
  )
}
