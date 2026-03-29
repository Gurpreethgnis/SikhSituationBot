'use client'

import React, { useState } from 'react'
import ChatInput from './components/ChatInput.jsx'
import Perspectives from './components/Perspectives.jsx'
import Logo from './components/Logo'
import MarkdownRenderer from './components/MarkdownRenderer'

function App() {
  const [persona, setPersona] = useState('adult')
  const [loading, setLoading] = useState(false)
  const [shabad, setShabad] = useState(null)
  const [aiResponse, setAiResponse] = useState('')

  const handleSend = async (query) => {
    setLoading(true)
    setShabad(null)
    setAiResponse('')

    try {
      // Use the Flask server URL if not in production or if NEXT_PUBLIC_API_URL is unset
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'
      const response = await fetch(`${apiUrl}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, persona }),
      })

      if (!response.ok) {
        throw new Error('Failed to fetch guidance')
      }

      const data = await response.json()
      setAiResponse(data.response)
      setShabad(data.shabad)
    } catch (error) {
      console.error('Error fetching guidance:', error)
      setAiResponse('Sorry, I am having trouble connecting to Gurbani wisdom right now. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app__header">
        <Logo />
        <h1 className="app__title">SikhSituationBot</h1>
        <p className="app__tagline">Gurbani-based guidance for life's moments</p>
      </header>

      <main className="app__main container">
        <Perspectives activePersona={persona} onPersonaChange={setPersona} />
        <ChatInput 
          onSend={handleSend} 
          placeholder={`Share how you're feeling as a ${persona}...`} 
          loading={loading}
        />

        {(aiResponse || loading) && (
          <div className="shabad-result">
            {loading ? (
              <div className="ai-insight-wrapper loading">
                <span className="insight-label">Seeking the Guru's wisdom...</span>
                <div className="loading-dots">
                  <span>.</span><span>.</span><span>.</span>
                </div>
              </div>
            ) : (
              <>
                <div className="ai-insight-wrapper">
                  <span className="insight-label">Guru's Guidance ({persona}):</span>
                  <div className="ai-insight">
                    <MarkdownRenderer content={aiResponse} />
                  </div>
                </div>
                {shabad && (
                  <div className={`shabad-card ${persona}`}>
                    <div className="ik-onkar-icon">☬</div>
                    <h2 className="gurmukhi-text">{shabad.text}</h2>
                    <p className="transliteration">{shabad.transliteration}</p>
                    <div className="shabad-divider"></div>
                    <p className="translation">“{shabad.title}”</p>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </main>

      <footer className="app__footer">
        <p>Seek guidance. Find peace.</p>
      </footer>
    </div>
  )
}

export default App
