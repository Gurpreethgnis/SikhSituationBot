'use client';
import { useState } from 'react';

export default function Home() {
  const [activePersona, setActivePersona] = useState('Adult');
  const [query, setQuery] = useState('');

  const personas = [
    { name: 'Child', icon: '👶' },
    { name: 'Teen', icon: '🎒' },
    { name: 'Adult', icon: '🧘' }
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log(`Searching for: "${query}" in persona: ${activePersona}`);
    // Future: API call to Flask backend
  };

  return (
    <main style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      padding: '2rem',
      textAlign: 'center'
    }}>
      <div style={{ marginBottom: '3rem' }}>
        <h1 className="gold-gradient-text" style={{
          fontSize: 'clamp(2.5rem, 8vw, 4.5rem)',
          fontWeight: '800',
          marginBottom: '1rem'
        }}>
          SikhSituationBot 🪯
        </h1>
        <p style={{
          color: 'var(--text-secondary)',
          fontSize: '1.2rem',
          maxWidth: '600px',
          margin: '0 auto',
          lineHeight: '1.6'
        }}>
          Find wisdom and guidance from Gurbani tailored specifically for your life's challenges.
        </p>
      </div>

      <div className="perspective-container" style={{ marginBottom: '2rem' }}>
        {personas.map((persona) => (
          <button
            key={persona.name}
            className={`perspective-pill ${activePersona === persona.name ? 'active' : ''}`}
            onClick={() => setActivePersona(persona.name)}
          >
            <span style={{ fontSize: '1.2rem' }}>{persona.icon}</span>
            {persona.name}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="chat-input-container">
        <input
          type="text"
          className="chat-input"
          placeholder="How are you feeling today? (e.g., 'I feel anxious about exams')"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" className="chat-submit-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </form>

      {/* Preview Wisdom Card (Visible for Demo) */}
      <article className={`shabad-card ${activePersona.toLowerCase()}`} style={{ marginTop: '3rem' }}>
        <header className="card-header">
          <div className="ik-onkar-icon">ੴ</div>
        </header>
        <section className="scripture-content">
          <h2 className="gurmukhi-text">ਤਿਥੈ ਤੂ ਸਮਰਥੁ ਜਿਥੈ ਕੋਇ ਨਾਹਿ ॥</h2>
          <p className="transliteration">Tithai tu samarathu jithai koi naahi ||</p>
          <blockquote className="translation">
            "Where there is no one else, You are all-powerful there."
          </blockquote>
        </section>
        <footer className="ai-insight">
          <div className="insight-label">AI Perspective: {activePersona}</div>
          <p className="insight-text">
            {activePersona === 'Child' ?
              "Just like a superhero who is always by your side, Guru Ji is with you even when you feel all alone. You are never actually by yourself!" :
              activePersona === 'Teen' ?
                "When you feel like no one understands what you're going through, remember there's a higher power that has your back 24/7. Use this Gurbani to ground yourself." :
                "This verse from Asa Ki Vaar reminds us of the omnipresence of the Divine. In moments of perceived isolation, we are invited to lean into the strength of the Creator."
            }
          </p>
        </footer>
      </article>

      <div style={{ marginTop: '4rem', opacity: 0.5, fontSize: '0.9rem' }}>
        <p>Built with ❤️ for the Panth</p>
      </div>
    </main>
  );
}
