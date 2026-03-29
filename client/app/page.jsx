'use client'

import React, { useState, useEffect, useRef } from 'react'
import ChatInput from './components/ChatInput.jsx'
import Perspectives from './components/Perspectives.jsx'
import Logo from './components/Logo'
import Sidebar from './components/Sidebar.jsx'
import MarkdownRenderer from './components/MarkdownRenderer'

function App() {
  const [persona, setPersona] = useState('adult')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState([])
  const [history, setHistory] = useState([])
  const [error, setError] = useState('')
  
  const messagesEndRef = useRef(null)

  // Scroll to bottom whenever messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  // Load history from localStorage on mount
  useEffect(() => {
    const savedHistory = localStorage.getItem('sikh_bot_history')
    if (savedHistory) {
      try {
        setHistory(JSON.parse(savedHistory))
      } catch (e) {
        console.error('Failed to parse history', e)
      }
    }
  }, [])

  // Save history to localStorage
  const saveToHistory = (query) => {
    const newHistoryItem = { 
      title: query.length > 30 ? query.substring(0, 30) + '...' : query,
      query: query,
      timestamp: new Date().toISOString()
    }
    const updatedHistory = [newHistoryItem, ...history.filter(h => h.query !== query)].slice(0, 20)
    setHistory(updatedHistory)
    localStorage.setItem('sikh_bot_history', JSON.stringify(updatedHistory))
  }

  const handleSend = async (query) => {
    setError('')
    setLoading(true)
    
    // Add user message to thread
    const userMessage = { role: 'user', content: query }
    setMessages(prev => [...prev, userMessage])
    saveToHistory(query)

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'
      const endpoint = `${baseUrl}/ask`
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, persona }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to fetch guidance: ${response.status}`)
      }

      const data = await response.json()
      
      // Add AI message to thread
      const aiMessage = { 
        role: 'assistant', 
        content: data.response,
        shabad: data.shabad,
        persona: data.persona
      }
      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('Chat query failed:', error)
      setError(`Sorry, I am having trouble connecting to Gurbani wisdom right now. (${error.message})`)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `Error: ${error.message}`, 
        isError: true 
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleNewChat = () => {
    setMessages([])
    setError('')
  }

  const handleSelectHistory = (historyItem) => {
    // For now, selecting history just starts a new query with that text
    setMessages([])
    handleSend(historyItem.query)
  }

  return (
    <div className="app-container">
      <Sidebar 
        history={history} 
        onSelectHistory={handleSelectHistory} 
        onNewChat={handleNewChat} 
      />

      <main className="chat-main">
        <header className="chat-header">
          <div className="chat-header__left">
            <h1 className="app__title--small">SikhSituationBot</h1>
          </div>
          <Perspectives activePersona={persona} onPersonaChange={setPersona} />
        </header>

        <section className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-welcome">
              <Logo />
              <h2>How can the Guru's wisdom help you today?</h2>
              <p>Seek guidance from the Siri Guru Granth Sahib Sahib Ji.</p>
            </div>
          )}

          {messages.map((msg, index) => (
            <div key={index} className={`message message--${msg.role}`}>
              <div className="message-label">
                {msg.role === 'user' ? 'You' : `Guru's Guidance (${msg.persona || persona})`}
              </div>
              <div className="message-content">
                {msg.role === 'assistant' ? (
                  <MarkdownRenderer content={msg.content} />
                ) : (
                  <p>{msg.content}</p>
                )}
                
                {msg.shabad && (
                  <div className={`shabad-card mini ${msg.persona || persona}`}>
                    <h2 className="gurmukhi-text">{msg.shabad.text}</h2>
                    <p className="translation">{msg.shabad.title}</p>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message message--assistant message--skeleton">
              <div className="message-label">Seeking Wisdom...</div>
              <div className="message-content">
                <div className="typing-dots"><span></span><span></span><span></span></div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </section>

        <footer className="chat-footer">
          <div className="chat-input-wrapper">
            <ChatInput
              onSend={handleSend}
              placeholder={`Share how you're feeling as a ${persona}...`}
              loading={loading}
            />
            <p className="footer-disclaimer">
              SikhSituationBot provides spiritual perspectives, not professional advice.
            </p>
          </div>
        </footer>
      </main>
    </div>
  )
}

export default App

