'use client'

import React, { useState } from 'react'
import ChatInput from './components/ChatInput.jsx'
import Perspectives from './components/Perspectives.jsx'

function App() {
  const [persona, setPersona] = useState('adult')

  const handleSend = (query) => {
    console.log(`Persona: ${persona} | Query: ${query}`)
    // TODO: Wire to backend / display results (task 3: chat flow)
  }

  return (
    <div className="app">
      <header className="app__header">
        <h1 className="app__title">SikhSituationBot</h1>
        <p className="app__tagline">Gurbani-based guidance for life's moments</p>
      </header>

      <main className="app__main">
        <Perspectives activePersona={persona} onPersonaChange={setPersona} />
        <ChatInput onSend={handleSend} placeholder={`Share how you're feeling as a ${persona}...`} />
      </main>

      <footer className="app__footer">
        <p>Seek guidance. Find peace.</p>
      </footer>
    </div>
  )
}

export default App
